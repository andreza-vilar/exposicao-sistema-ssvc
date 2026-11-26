#!/usr/bin/env python3
"""Camada CP02.1: visão global ou seleção explícita, sem novas regras SSVC.

Somente arquivos locais do projeto; nenhuma coleta AWS/Kubernetes. O workload
é uma unidade operacional provisória, não uma definição normativa do SSVC.
"""
from collections import Counter
from copy import deepcopy
import argparse
import hashlib
import json
from pathlib import Path
import sys

import exposure_analyzer as legacy
from run_experiments import local_path, validate_cloud

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = '1.0.0'
SUPPORTED_KINDS = ('Deployment', 'StatefulSet', 'DaemonSet', 'ReplicaSet', 'Pod')
LIMITATIONS = [
    'Workload é unidade operacional provisória; não equivale automaticamente ao componente vulnerável do SSVC.',
    'O conjunto de manifestos não define necessariamente a fronteira normativa de um sistema.',
    'Categorias, evidências, correlações e confiança heurística são as do classificador histórico, sem revisão de regras.',
    'Confiança low/medium/high é heurística legada, não probabilidade calibrada; não existe confiança global legada.',
    'Não há associação CVE/biblioteca/função vulnerável nem coleta ou validação operacional de infraestrutura.',
]


class InputError(ValueError):
    def __init__(self, code, message, **details):
        super().__init__(message)
        self.code = code
        self.details = details


def classifier_identity():
    return {
        'id': 'legacy-exposure-analyzer',
        'sha256': hashlib.sha256((ROOT / 'src' / 'exposure_analyzer.py').read_bytes()).hexdigest(),
        'adapter_id': 'cp02.1-workload-selection',
        'adapter_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }


def envelope(mode, target):
    return {
        'schema_version': SCHEMA_VERSION,
        'classifier': classifier_identity(),
        'mode': mode,
        'selected_unit': {'type': 'manifest_set' if mode == 'system' else 'workload',
                          'identifier': target if mode == 'target' else None},
        'selected_exposure': None,
        'selected_result': None,
        'selected_legacy_confidence': None,
        'global_exposure': None,
        'aggregation': {
            'global_strategy': 'legacy_ordinal_maximum', 'order': list(legacy.LEVELS),
            'global_scope': 'all_supported_workloads_in_input',
            'selected_strategy': 'exact_workload_lookup' if mode == 'target' else 'legacy_ordinal_maximum',
            'normative_system_boundary_assumed': False,
        },
        'workloads_found': [],
        'global_result': None,
        'inputs': None,
        'status': 'error',
        'errors': [],
        'limitations': list(LIMITATIONS),
    }


def record_error(result, exc):
    result['status'] = 'error'
    result['errors'].append({'code': exc.code, 'message': str(exc), 'details': exc.details})
    return result


def workload_ids(objects):
    """Validar identidade sem reimplementar qualquer regra de exposição."""
    if not isinstance(objects, list) or any(not isinstance(o, dict) for o in objects):
        raise InputError('invalid_objects', 'Entrada deve ser lista de objetos Kubernetes.')
    ids = []
    for obj in objects:
        if obj.get('kind') not in SUPPORTED_KINDS:
            continue
        metadata = obj.get('metadata', {})
        if not isinstance(metadata, dict):
            raise InputError('invalid_workload_identity', 'metadata do workload deve ser objeto.')
        kind = obj['kind']
        namespace, name = metadata.get('namespace', 'default'), metadata.get('name')
        if any(not isinstance(v, str) or not v or v.strip() != v or '/' in v
               for v in (namespace, name)):
            raise InputError('invalid_workload_identity',
                             'Workload requer namespace e nome textuais não vazios; namespace omitido usa default.')
        ids.append('%s/%s/%s' % (kind, namespace, name))
    return ids


def analyze_units(objects, cloud=None, mode='system', target=None):
    """API pura de seleção: uma chamada à análise completa; sem filtrar seus inputs.

    Resultado determinístico para as mesmas entradas e hashes de código. Não
    altera objetos do chamador. cloud, quando fornecido, é Cloud offline legado.
    """
    result = envelope(mode, target)
    try:
        if mode not in ('system', 'target'):
            raise InputError('invalid_mode', 'Modo deve ser system ou target.')
        if mode == 'system' and target is not None:
            raise InputError('unexpected_target', 'System mode não aceita --target.')
        ids = workload_ids(objects)
        result['workloads_found'] = ids
        counts = Counter(ids)
        duplicates = {identity: count for identity, count in sorted(counts.items()) if count > 1}
        if duplicates:
            code = 'ambiguous_target' if mode == 'target' and isinstance(target, str) and target in duplicates else 'duplicate_workload_identities'
            raise InputError(code, 'Identidades duplicadas impedem seleção e contexto global não ambíguos.',
                             duplicates=duplicates)
        if not ids:
            raise InputError('no_supported_workloads', 'Nenhum workload suportado encontrado.',
                             supported_kinds=list(SUPPORTED_KINDS))

        global_result = legacy.analyze(deepcopy(objects), deepcopy(cloud))
        result['global_result'] = global_result
        result['global_exposure'] = global_result['system_exposure']
        if mode == 'system':
            result['selected_exposure'] = result['global_exposure']
        else:
            if not isinstance(target, str) or len(target.split('/')) != 3 or any(
                not part or part.strip() != part for part in target.split('/')
            ):
                raise InputError('invalid_target_identifier', 'Informe o alvo completo Kind/namespace/nome.')
            selected = [w for w in global_result['workloads'] if w['workload'] == target]
            if not selected:
                raise InputError('target_not_found', 'O alvo exato não foi encontrado; nenhum substituto foi selecionado.',
                                 requested_target=target)
            # As identidades já foram verificadas antes de executar o legado.
            if len(selected) != 1:
                raise InputError('ambiguous_target', 'Mais de um resultado corresponde ao alvo.', requested_target=target)
            result['selected_result'] = deepcopy(selected[0])
            result['selected_exposure'] = selected[0]['exposure']
            result['selected_legacy_confidence'] = selected[0]['confidence']
        result['status'] = 'ok'
    except InputError as exc:
        record_error(result, exc)
    except Exception as exc:
        record_error(result, InputError('legacy_analysis_error', 'Falha na análise histórica: ' + str(exc),
                                        exception_type=type(exc).__name__))
    return result


def manifest_files(path):
    """Descoberta restrita, rejeitando symlinks antes de percorrer diretórios."""
    path = local_path(path)
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise InputError('manifest_path_not_found', 'Arquivo ou diretório de manifestos não encontrado.')
    files = []
    for child in sorted(path.iterdir()):
        child = local_path(child)
        if child.is_dir():
            files.extend(manifest_files(child))
        elif child.is_file() and child.suffix in ('.yaml', '.yml'):
            files.append(child)
    return sorted(files)


def analyze_files(manifests, cloud_path=None, mode='system', target=None):
    """CLI/API de arquivos: JSON/YAML locais; delega parser e motor históricos."""
    inputs = {'manifests': [], 'snapshot': None}
    try:
        files = manifest_files(manifests)
        if not files:
            raise InputError('no_manifest_files', 'Nenhum arquivo YAML encontrado no diretório.')
        objects = []
        for path in files:
            before = path.read_bytes()
            inputs['manifests'].append({'path': str(path.relative_to(ROOT)),
                                        'sha256': hashlib.sha256(before).hexdigest()})
            objects.extend(legacy.load_manifests(path))
            if path.read_bytes() != before:
                raise InputError('input_changed', 'Manifesto mudou durante a leitura.')
        cloud = None
        if cloud_path is not None:
            path = local_path(cloud_path)
            data = path.read_bytes()
            inputs['snapshot'] = {'path': str(path.relative_to(ROOT)),
                                  'sha256': hashlib.sha256(data).hexdigest(), 'origin': 'synthetic'}
            cloud = legacy.Cloud(validate_cloud(json.loads(data)))
        result = analyze_units(objects, cloud, mode, target)
    except Exception as exc:
        result = envelope(mode, target)
        error = exc if isinstance(exc, InputError) else InputError(
            'input_error', 'Falha na entrada local: ' + str(exc), exception_type=type(exc).__name__)
        record_error(result, error)
    result['inputs'] = inputs
    return result


def render_text(result):
    lines = ['STATUS: ' + result['status'], 'MODO: ' + str(result['mode']),
             'UNIDADE SOLICITADA: ' + str(result['selected_unit']),
             'EXPOSIÇÃO SELECIONADA: ' + str(result['selected_exposure']),
             'EXPOSIÇÃO GLOBAL (contexto): ' + str(result['global_exposure']),
             'AGREGAÇÃO GLOBAL: legacy_ordinal_maximum; fronteira normativa não assumida.']
    for error in result['errors']:
        lines.append('ERRO %s: %s' % (error['code'], error['message']))
    if result['global_result'] is not None:
        lines.extend(['', 'CONTEXTO COMPLETO — saída histórica:', legacy.render_text(result['global_result'])])
    lines.extend(['', 'LIMITAÇÕES:'] + ['- ' + text for text in result['limitations']])
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifests', required=True, type=Path)
    parser.add_argument('--cloud', type=Path, help='JSON sintético local opcional')
    parser.add_argument('--mode', default='system', help='system ou target')
    parser.add_argument('--target', help='Kind/namespace/nome exato, somente em target mode')
    parser.add_argument('--format', choices=('json', 'text'), default='text')
    args = parser.parse_args(argv)
    result = analyze_files(args.manifests, args.cloud, args.mode, args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == 'json' else render_text(result))
    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())
