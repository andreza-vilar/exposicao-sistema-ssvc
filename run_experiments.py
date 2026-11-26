#!/usr/bin/env python3
"""Comparação offline B1/B2 do classificador histórico, sem alterar suas regras.

Entradas/saídas ficam dentro deste repositório. Snapshots são JSONs sintéticos.
Sem SDKs, rede, subprocessos, consultas Git ou descoberta de credenciais.
"""
import argparse
from collections import Counter
from copy import deepcopy
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
from time import perf_counter

import yaml
from exposure_analyzer import Cloud, LEVELS, RANK, analyze, load_manifests

ROOT = Path(__file__).resolve().parent
CLASSIFIER = ROOT / 'exposure_analyzer.py'
CONFIDENCE_NOTE = 'Confiança heurística legada (low/medium/high), não calibrada.'
LIMITATION = 'Concordância com rótulos sintéticos históricos; não é acurácia científica.'


def local_path(path):
    """Recusar escapes antes de abrir arquivo ou descobrir cenários."""
    path = Path(path).absolute()
    # Resolver symlinks só depois de conferir os componentes lexicais locais.
    if '..' in path.parts or not (path == ROOT or ROOT in path.parents):
        raise ValueError('Caminho deve permanecer dentro do repositório acadêmico')
    current = ROOT
    for part in path.relative_to(ROOT).parts:
        current = current / part
        if current.is_symlink():
            raise ValueError('Links simbólicos não são aceitos nas entradas/saídas')
    return path


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_input(path):
    return local_path(path).read_bytes()


def discover_scenarios(root):
    root = local_path(root)
    if not root.is_dir():
        raise ValueError('Diretório de cenários não encontrado')
    found = [p for p in sorted(root.iterdir()) if p.is_dir() or p.is_symlink()]
    if not found:
        raise ValueError('Nenhum cenário encontrado')
    return found


def validate_cloud(data):
    """Validar forma local do subconjunto aceito, não completude operacional AWS."""
    if not isinstance(data, dict) or not any(k in data for k in ('LoadBalancers', 'SecurityGroups', 'Nodes')):
        raise ValueError('Snapshot deve ser objeto com LoadBalancers, SecurityGroups ou Nodes')
    for key in ('LoadBalancers', 'SecurityGroups', 'Nodes'):
        values = data.get(key, [])
        if not isinstance(values, list) or any(not isinstance(v, dict) for v in values):
            raise ValueError('%s deve ser lista de objetos' % key)
    for lb in data.get('LoadBalancers', []):
        if not all(isinstance(lb.get(k), str) and lb[k] for k in ('DNSName', 'Scheme')):
            raise ValueError('LB deve informar DNSName e Scheme')
        if lb['Scheme'] not in ('internal', 'internet-facing'):
            raise ValueError('Scheme inválido')
        if not isinstance(lb.get('SecurityGroups', []), list):
            raise ValueError('SecurityGroups de LB deve ser lista')
    for sg in data.get('SecurityGroups', []):
        if not isinstance(sg.get('GroupId'), str) or not sg['GroupId']:
            raise ValueError('SG deve informar GroupId')
        permissions = sg.get('IpPermissions', [])
        if not isinstance(permissions, list) or any(not isinstance(p, dict) for p in permissions):
            raise ValueError('IpPermissions deve ser lista de objetos')
        for perm in permissions:
            for key in ('FromPort', 'ToPort'):
                if key in perm and type(perm[key]) is not int:
                    raise ValueError('Porta de SG deve ser inteira')
            for key, field in (('IpRanges', 'CidrIp'), ('Ipv6Ranges', 'CidrIpv6')):
                ranges = perm.get(key, [])
                if not isinstance(ranges, list) or any(
                    not isinstance(r, dict) or not isinstance(r.get(field), str) for r in ranges
                ):
                    raise ValueError('%s deve conter CIDRs textuais' % key)
    for node in data.get('Nodes', []):
        if not isinstance(node.get('SecurityGroupIds', []), list):
            raise ValueError('SecurityGroupIds deve ser lista')
    return data


def error_info(exc, phase):
    return {'phase': phase, 'type': type(exc).__name__, 'message': str(exc)}


def base_record(scenario, configuration, metadata):
    return {
        'scenario_id': scenario, 'configuration': configuration,
        'classifier_sha256': metadata['classifier_sha256'],
        'python_version': metadata['python_version'], 'pyyaml_version': metadata['pyyaml_version'],
        'manifest_path': None, 'manifest_sha256': None,
        'snapshot_path': None, 'snapshot_sha256': None,
        'snapshot_validation': 'not_used' if configuration == 'B1' else 'not_checked',
        'snapshot_origin': 'synthetic' if configuration == 'B2' else None,
        'historical_label': None, 'historical_label_sha256': None,
        'classification': None, 'legacy_confidence_by_workload': [],
        'confidence_semantics': CONFIDENCE_NOTE, 'result': None,
        'status': 'error', 'not_applicable_reason': None, 'errors': [],
        'classification_attempted': False,
        'classifier_elapsed_seconds': None, 'elapsed_seconds': 0.0,
    }


def evaluate_scenario(directory, metadata):
    """Capturar entradas uma vez, analisar cópias idênticas e preservar output integral."""
    records = [base_record(directory.name, c, metadata) for c in ('B1', 'B2')]
    b1, b2 = records
    started = perf_counter()
    snapshot = directory / 'cloud.json'
    try:
        directory = local_path(directory)
        manifest = local_path(directory / 'manifests.yaml')
        for record in records:
            record['manifest_path'] = str(manifest.relative_to(ROOT))
        manifest_bytes = read_input(manifest)
        for record in records:
            record['manifest_sha256'] = sha256(manifest_bytes)
        # Reutiliza o parser histórico. O hash antes/depois detecta alteração durante leitura.
        objects = load_manifests(manifest)
        if read_input(manifest) != manifest_bytes:
            raise ValueError('Manifesto mudou durante a leitura')
        if not objects or any(not isinstance(o, dict) for o in objects):
            raise ValueError('Manifestos devem conter objetos Kubernetes')
    except Exception as exc:
        for record in records:
            record['errors'].append(error_info(exc, 'manifests'))
        objects = None

    # Rótulo histórico não é entrada do classificador. Sua falha não impede a análise.
    try:
        label_bytes = read_input(directory / 'expected.json')
        label = json.loads(label_bytes)['system_exposure']
        if label not in LEVELS:
            raise ValueError('Rótulo histórico inválido')
        for record in records:
            record['historical_label'] = label
            record['historical_label_sha256'] = sha256(label_bytes)
    except Exception as exc:
        for record in records:
            record['errors'].append(error_info(exc, 'historical_label'))

    cloud_data = None
    snapshot_problem = False
    try:
        snapshot = local_path(snapshot)
        if not snapshot.exists():
            b2['snapshot_validation'] = 'missing'
            b2['status'] = 'not_applicable'
            b2['not_applicable_reason'] = 'snapshot_missing'
        else:
            b2['snapshot_path'] = str(snapshot.relative_to(ROOT))
            snapshot_bytes = read_input(snapshot)
            b2['snapshot_sha256'] = sha256(snapshot_bytes)
            cloud_data = validate_cloud(json.loads(snapshot_bytes))
            b2['snapshot_validation'] = 'valid_structural_subset'
    except Exception as exc:
        snapshot_problem = True
        b2['snapshot_validation'] = 'invalid'
        b2['errors'].append(error_info(exc, 'snapshot'))

    preparation_elapsed = perf_counter() - started
    for record in records:
        tick = perf_counter()
        should_run = objects is not None and (
            record['configuration'] == 'B1' or (cloud_data is not None and not snapshot_problem)
        )
        if should_run:
            record['classification_attempted'] = True
            try:
                cloud = Cloud(deepcopy(cloud_data)) if record['configuration'] == 'B2' else None
                analysis_tick = perf_counter()
                output = analyze(deepcopy(objects), cloud)
                record['classifier_elapsed_seconds'] = perf_counter() - analysis_tick
                record['result'] = output
                if output.get('system_exposure') not in LEVELS or not output.get('workloads'):
                    raise ValueError('Classificador não produziu classificação/workloads válidos')
                record['classification'] = output['system_exposure']
                record['legacy_confidence_by_workload'] = [
                    {'workload': w['workload'], 'confidence': w['confidence']}
                    for w in output['workloads']
                ]
                # Erro no rótulo é erro da execução experimental, preservando a classificação.
                record['status'] = 'ok' if not record['errors'] else 'error'
            except Exception as exc:
                record['errors'].append(error_info(exc, 'classification'))
                record['status'] = 'error'
        if record['errors'] and record['status'] != 'not_applicable':
            record['status'] = 'error'
        record['elapsed_seconds'] = preparation_elapsed + perf_counter() - tick
    return records


def confidence_map(record):
    return {w['workload']: w['confidence'] for w in record['legacy_confidence_by_workload']}


def evidence_set(record):
    return sorted({e for w in record['result']['workloads'] for p in w['entrypoints'] for e in p['evidence']})


def pair_results(records):
    grouped = {}
    for record in records:
        grouped.setdefault(record['scenario_id'], {})[record['configuration']] = record
    pairs = []
    for sid, group in sorted(grouped.items()):
        b1, b2 = group['B1'], group['B2']
        if b1['status'] != 'ok' or b2['status'] != 'ok':
            continue
        if b1['manifest_sha256'] != b2['manifest_sha256']:
            raise ValueError('Par com manifestos diferentes: ' + sid)
        l1, l2, expected = b1['classification'], b2['classification'], b1['historical_label']
        direction = 'increase' if RANK[l2] > RANK[l1] else 'decrease' if RANK[l2] < RANK[l1] else 'unchanged'
        c1, c2 = confidence_map(b1), confidence_map(b2)
        match1, match2 = l1 == expected, l2 == expected
        pairs.append({
            'scenario_id': sid, 'manifest_sha256': b1['manifest_sha256'],
            'b1_manifest_sha256': b1['manifest_sha256'], 'b2_manifest_sha256': b2['manifest_sha256'],
            'snapshot_sha256': b2['snapshot_sha256'], 'historical_label': expected,
            'b1_classification': l1, 'b2_classification': l2,
            'b1_legacy_confidence': c1, 'b2_legacy_confidence': c2,
            'category_changed': l1 != l2, 'ordinal_direction': direction,
            'confidence_changed': c1 != c2,
            'change_group': direction if l1 != l2 else 'confidence_only' if c1 != c2 else 'unchanged',
            'b1_matches_historical': match1, 'b2_matches_historical': match2,
            'historical_agreement_change': 'gained' if match2 and not match1 else 'lost' if match1 and not match2 else 'unchanged',
            'evidence_removed_from_b1': sorted(set(evidence_set(b1)) - set(evidence_set(b2))),
            'evidence_added_in_b2': sorted(set(evidence_set(b2)) - set(evidence_set(b1))),
            'evidence_interpretation': 'Diferença textual de evidências, não prova causal automática.',
        })
    return pairs


def ratio(numerator, denominator):
    return {'numerator': numerator, 'denominator': denominator,
            'proportion': numerator / denominator if denominator else None}


def metrics(records):
    ok = [r for r in records if r['status'] == 'ok']
    labelled = [r for r in ok if r['historical_label'] in LEVELS]
    counts = Counter(r['classification'] for r in ok)
    return {
        'records': len(records), 'successful_executions': len(ok),
        'classification_attempts': sum(r['classification_attempted'] for r in records),
        'status_counts': {s: sum(r['status'] == s for r in records) for s in ('ok', 'not_applicable', 'error')},
        'category_distribution': {level: counts[level] for level in LEVELS},
        'historical_agreement': ratio(sum(r['classification'] == r['historical_label'] for r in labelled), len(labelled)),
        'underestimates_vs_historical': ratio(sum(RANK[r['classification']] < RANK[r['historical_label']] for r in labelled), len(labelled)),
        'overestimates_vs_historical': ratio(sum(RANK[r['classification']] > RANK[r['historical_label']] for r in labelled), len(labelled)),
        'classifier_elapsed_seconds_sum': sum(r['classifier_elapsed_seconds'] or 0 for r in records),
    }


def summarize(records, pairs, metadata, wall_seconds):
    paired_ids = {p['scenario_id'] for p in pairs}
    transition = {a: {b: 0 for b in LEVELS} for a in LEVELS}
    for pair in pairs:
        transition[pair['b1_classification']][pair['b2_classification']] += 1
    groups = Counter(p['change_group'] for p in pairs)
    return {
        'schema_version': '1.0', 'metadata': metadata,
        'total_scenarios': len({r['scenario_id'] for r in records}),
        'b2_snapshot_files': sum(r['snapshot_sha256'] is not None for r in records if r['configuration'] == 'B2'),
        'b2_valid_snapshots': sum(r['snapshot_validation'] == 'valid_structural_subset' for r in records if r['configuration'] == 'B2'),
        'eligible_pairs': len(pairs),
        'all_scenarios': {c: metrics([r for r in records if r['configuration'] == c]) for c in ('B1', 'B2')},
        'paired_subset': {c: metrics([r for r in records if r['configuration'] == c and r['scenario_id'] in paired_ids]) for c in ('B1', 'B2')},
        'transition_b1_to_b2': transition,
        'category_changes': ratio(sum(p['category_changed'] for p in pairs), len(pairs)),
        'change_groups': {g: groups[g] for g in ('increase', 'decrease', 'confidence_only', 'unchanged')},
        'historical_agreement_changes': {g: sum(p['historical_agreement_change'] == g for p in pairs) for g in ('gained', 'lost', 'unchanged')},
        'non_applicable': [{'scenario_id': r['scenario_id'], 'configuration': r['configuration'], 'reason': r['not_applicable_reason']} for r in records if r['status'] == 'not_applicable'],
        'errors': [{'scenario_id': r['scenario_id'], 'configuration': r['configuration'], 'errors': r['errors']} for r in records if r['errors']],
        'wall_elapsed_seconds': wall_seconds,
        'timing_semantics': 'Tempos variam; wall exclui exportação; soma classifier mede análise+cópia. elapsed individual inclui preparação compartilhada e não é aditivo.',
        'interpretation': LIMITATION,
        'ordinal_semantics': 'Small < Controlled < Open indica direção; não escala quantitativa de risco.',
        'b0_status': 'pending_author_confirmation_not_executed',
    }


def run_experiment(scenarios_root=ROOT / 'scenarios'):
    started = perf_counter()
    metadata = {
        'classifier_sha256': sha256(read_input(CLASSIFIER)),
        'executor_sha256': sha256(read_input(Path(__file__))),
        'python_version': sys.version.split()[0], 'pyyaml_version': yaml.__version__,
        'created_at_utc': datetime.now(timezone.utc).isoformat(),
        'scenarios_root': str(local_path(scenarios_root).relative_to(ROOT)),
        'snapshot_origin': 'synthetic', 'confidence_semantics': CONFIDENCE_NOTE,
        'manifest_annotations_available_in_b1': True,
        'unit_of_analysis': 'legacy_workload_and_system_maximum',
    }
    records = []
    for directory in discover_scenarios(scenarios_root):
        records.extend(evaluate_scenario(directory, metadata))
    if sha256(read_input(CLASSIFIER)) != metadata['classifier_sha256']:
        raise ValueError('Classificador mudou durante execução')
    pairs = pair_results(records)
    summary = summarize(records, pairs, metadata, perf_counter() - started)
    return records, pairs, summary


def format_rate(rate):
    return '%d/%d%s' % (rate['numerator'], rate['denominator'],
                        ' (%.1f%%)' % (100 * rate['proportion']) if rate['proportion'] is not None else ' (não aplicável)')


def render_report(records, pairs, summary):
    lines = ['# CP01.2 — Comparação preliminar B1 × B2', '',
             LIMITATION, '', CONFIDENCE_NOTE, '',
             'B0 pendente de confirmação com Jan; não executado. Classificador histórico preservado.', '',
             '## Protocolo e arquitetura', '',
             'Descoberta local → leitura/hash/validação → parser histórico → cópias dos mesmos objetos para B1/B2 → análise histórica → pareamento → métricas → exportação.', '',
             'B1 mantém annotations AWS do manifesto. B2 acrescenta somente JSON sintético. Nenhum YAML foi aplicado e nenhum snapshot foi obtido de serviço real.', '',
             'Hashes e versões: `summary.json`; outputs completos e evidências: `raw_results.json`; diferenças textuais de evidência: `paired_comparison.csv`.', '',
             '## Execuções individuais', '',
             '| Cenário | Histórico | B1 / confiança por workload | B2 / confiança por workload | Status B2 |',
             '|---|---|---|---|---|']
    indexed = {}
    for r in records:
        indexed.setdefault(r['scenario_id'], {})[r['configuration']] = r
    for sid, group in sorted(indexed.items()):
        a, b = group['B1'], group['B2']
        lines.append('| %s | %s | %s / %s | %s / %s | %s |' % (
            sid, a['historical_label'], a['classification'], json.dumps(confidence_map(a), ensure_ascii=False),
            b['classification'], json.dumps(confidence_map(b), ensure_ascii=False), b['status']))
    lines.extend(['', '## Pares elegíveis', '',
                  '| Cenário | B1 → B2 | Grupo | Concordância histórica |', '|---|---|---|---|'])
    for p in pairs:
        lines.append('| %s | %s → %s | %s | %s |' % (
            p['scenario_id'], p['b1_classification'], p['b2_classification'], p['change_group'], p['historical_agreement_change']))
    lines.extend(['', '## Métricas e denominadores', '',
                  '| Conjunto | Configuração | Execuções OK | Small / Controlled / Open | Concordância histórica | Subestimativas | Superestimativas |',
                  '|---|---|---|---|---|---|---|'])
    for scope in ('all_scenarios', 'paired_subset'):
        for c in ('B1', 'B2'):
            m = summary[scope][c]
            lines.append('| %s | %s | %d | %s | %s | %s | %s |' % (
                scope, c, m['successful_executions'], ' / '.join(str(m['category_distribution'][l]) for l in LEVELS),
                format_rate(m['historical_agreement']), format_rate(m['underestimates_vs_historical']),
                format_rate(m['overestimates_vs_historical'])))
    lines.extend(['', 'Matriz B1 → B2 (linhas B1; colunas B2):', '',
                  '| B1 / B2 | small | controlled | open |', '|---|---|---|---|'])
    for level in LEVELS:
        lines.append('| %s | %s |' % (level, ' | '.join(str(summary['transition_b1_to_b2'][level][b]) for b in LEVELS)))
    lines.extend(['', 'Mudanças de categoria: ' + format_rate(summary['category_changes']) + '.',
                  'Grupos mutuamente exclusivos: `' + json.dumps(summary['change_groups'], ensure_ascii=False) + '`.', '',
                  '## Não aplicáveis e erros', ''])
    for r in records:
        if r['status'] != 'ok' or r['errors']:
            lines.append('- %s / %s: %s; motivo=%s; erros=%s' % (
                r['scenario_id'], r['configuration'], r['status'], r['not_applicable_reason'], json.dumps(r['errors'], ensure_ascii=False)))
    if not summary['errors']:
        lines.append('Nenhum erro de entrada ou classificação registrado.')
    lines.extend(['', '## Diferenças de evidências e interpretação', ''])
    for p in pairs:
        lines.append('### ' + p['scenario_id'])
        lines.append('Categoria: %s → %s; confiança legada: %s → %s.' % (
            p['b1_classification'], p['b2_classification'], p['b1_legacy_confidence'], p['b2_legacy_confidence']))
        for evidence in p['evidence_added_in_b2']:
            lines.append('- Evidência adicionada: ' + evidence)
        for evidence in p['evidence_removed_from_b1']:
            lines.append('- Evidência substituída/retirada: ' + evidence)
        lines.append('')
    lines.extend(['## Limitações', '',
                  '- Corpus pequeno, sintético e com rótulos definidos pelo autor; B2 não é gabarito de B1.',
                  '- Comparação pareada usa somente execuções OK de ambos os modos; não aplicáveis e erros permanecem exportados.',
                  '- Unidade e máximo global são os do classificador legado; nenhuma revisão científica das regras foi implementada.',
                  '- Confiança high não é evidência de acerto ou probabilidade calibrada; a diferença de strings não prova causalidade.',
                  '- O executor não cria indicadores novos de suficiência/fallback. Validação JSON é estrutural, não verificação de infraestrutura.',
                  '- Tempos e timestamp variam; classificações e métricas categóricas são determinísticas para as mesmas entradas.', '',
                  'Tempo total antes da exportação: %.6f s.' % summary['wall_elapsed_seconds'], ''])
    return '\n'.join(lines)


def export_results(output_dir, records, pairs, summary):
    output_dir = local_path(output_dir)
    # Reserva exclusiva: nunca sobrescrever ou misturar com rodada anterior.
    output_dir.mkdir(parents=True, exist_ok=False)
    raw = {'schema_version': '1.0', 'metadata': summary['metadata'], 'executions': records}
    documents = {
        'raw_results.json': json.dumps(raw, indent=2, ensure_ascii=False) + '\n',
        'summary.json': json.dumps(summary, indent=2, ensure_ascii=False) + '\n',
        'report.md': render_report(records, pairs, summary),
    }
    columns = list(pairs[0]) if pairs else [
        'scenario_id', 'manifest_sha256', 'b1_manifest_sha256', 'b2_manifest_sha256',
        'snapshot_sha256', 'historical_label', 'b1_classification', 'b2_classification',
        'b1_legacy_confidence', 'b2_legacy_confidence', 'category_changed', 'ordinal_direction',
        'confidence_changed', 'change_group', 'b1_matches_historical', 'b2_matches_historical',
        'historical_agreement_change', 'evidence_removed_from_b1', 'evidence_added_in_b2', 'evidence_interpretation',
    ]
    csv_buffer = io.StringIO(newline='')
    writer = csv.DictWriter(csv_buffer, fieldnames=columns)
    writer.writeheader()
    for pair in pairs:
        writer.writerow({k: json.dumps(v, ensure_ascii=False, sort_keys=True) if isinstance(v, (dict, list)) else v for k, v in pair.items()})
    documents['paired_comparison.csv'] = csv_buffer.getvalue()
    for name, content in documents.items():
        with (output_dir / name).open('x', encoding='utf-8', newline='') as stream:
            stream.write(content)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', type=Path, default=ROOT / 'scenarios')
    parser.add_argument('--output', type=Path, default=ROOT / 'results' / 'cp01.2')
    args = parser.parse_args(argv)
    try:
        output = local_path(args.output)
        if output.exists():
            raise FileExistsError('Diretório de resultados já existe; escolha outro --output')
        records, pairs, summary = run_experiment(args.scenarios)
        export_results(output, records, pairs, summary)
    except Exception as exc:
        print('Erro experimental: %s: %s' % (type(exc).__name__, exc), file=sys.stderr)
        return 1
    print('Cenários: %d; B1 OK: %d; B2 OK: %d; pares: %d' % (
        summary['total_scenarios'], summary['all_scenarios']['B1']['successful_executions'],
        summary['all_scenarios']['B2']['successful_executions'], summary['eligible_pairs']))
    for c in ('B1', 'B2'):
        print('%s pareado: %s' % (c, format_rate(summary['paired_subset'][c]['historical_agreement'])))
    print('Mudanças de categoria: ' + format_rate(summary['category_changes']))
    print('Grupos: ' + json.dumps(summary['change_groups'], ensure_ascii=False))
    print('Não aplicáveis: %d; registros com erros: %d' % (len(summary['non_applicable']), len(summary['errors'])))
    print(LIMITATION)
    print('Resultados: ' + str(output.relative_to(ROOT)))
    return 1 if summary['errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
