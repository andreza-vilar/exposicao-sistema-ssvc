"""Testes offline do executor; temporários ficam somente em tests/ no projeto."""
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import run_experiments as exp
from tools.offline_python import audit


MANIFEST = '''apiVersion: v1
kind: Pod
metadata: {name: app, namespace: demo, labels: {app: web}}
spec: {containers: [{name: app, image: synthetic}]}
---
apiVersion: v1
kind: Service
metadata: {name: web, namespace: demo}
spec:
  type: NodePort
  selector: {app: web}
  ports: [{port: 80, nodePort: 30080}]
'''


class ExperimentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='cp01_2_', dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.scenarios = self.root / 'scenarios'
        self.scenarios.mkdir()

    def scenario(self, name='01-test', cloud=None, expected='open', manifest=MANIFEST):
        path = self.scenarios / name
        path.mkdir()
        (path / 'manifests.yaml').write_text(manifest, encoding='utf-8')
        (path / 'expected.json').write_text(json.dumps({'system_exposure': expected}), encoding='utf-8')
        if cloud is not None:
            (path / 'cloud.json').write_text(json.dumps(cloud), encoding='utf-8')
        return path

    def run_cli(self, output):
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            return exp.main(['--scenarios', str(self.scenarios), '--output', str(output)])

    def test_discovery_sorted_and_ignores_files(self):
        self.scenario('02-b')
        self.scenario('01-a')
        (self.scenarios / 'README.txt').write_text('local')
        self.assertEqual([p.name for p in exp.discover_scenarios(self.scenarios)], ['01-a', '02-b'])

    def test_missing_snapshot_not_run_or_paired(self):
        self.scenario()
        with patch.object(exp, 'analyze', wraps=exp.analyze) as analyze:
            records, pairs, summary = exp.run_experiment(self.scenarios)
        self.assertEqual(analyze.call_count, 1)
        self.assertEqual(records[0]['classification'], 'open')
        self.assertEqual(records[1]['status'], 'not_applicable')
        self.assertEqual(records[1]['not_applicable_reason'], 'snapshot_missing')
        self.assertIsNone(records[1]['classification'])
        self.assertIsNone(records[1]['snapshot_sha256'])
        self.assertEqual(pairs, [])
        self.assertIsNone(summary['category_changes']['proportion'])

    def test_valid_snapshot_same_manifest_separate_cloud(self):
        self.scenario(cloud={'Nodes': [{'InstanceId': 'synthetic-private-node'}]}, expected='controlled')
        received = []
        original = exp.analyze

        def spy(objects, cloud):
            received.append((deepcopy(objects), cloud))
            return original(objects, cloud)

        with patch.object(exp, 'analyze', side_effect=spy):
            records, pairs, summary = exp.run_experiment(self.scenarios)
        self.assertEqual(received[0][0], received[1][0])
        self.assertIsNone(received[0][1])
        self.assertIsInstance(received[1][1], exp.Cloud)
        self.assertEqual(records[0]['manifest_sha256'], records[1]['manifest_sha256'])
        self.assertEqual(pairs[0]['ordinal_direction'], 'decrease')
        self.assertEqual(pairs[0]['historical_agreement_change'], 'gained')
        self.assertEqual(summary['transition_b1_to_b2']['open']['controlled'], 1)
        self.assertEqual(records[1]['snapshot_origin'], 'synthetic')

    def test_metrics_use_same_paired_denominator(self):
        self.scenario('01-private', cloud={'Nodes': [{}]}, expected='controlled')
        self.scenario('02-no-cloud')
        _, _, s = exp.run_experiment(self.scenarios)
        self.assertEqual(s['all_scenarios']['B1']['historical_agreement'], exp.ratio(1, 2))
        self.assertEqual(s['all_scenarios']['B2']['historical_agreement'], exp.ratio(1, 1))
        self.assertEqual(s['paired_subset']['B1']['historical_agreement'], exp.ratio(0, 1))
        self.assertEqual(s['paired_subset']['B2']['historical_agreement'], exp.ratio(1, 1))
        self.assertEqual(s['all_scenarios']['B1']['overestimates_vs_historical'], exp.ratio(1, 2))
        self.assertEqual(s['eligible_pairs'], 1)

    def test_transition_increase_decrease_and_confidence_only(self):
        fixtures = [('a', 'small', 'open', 'low', 'high', 'increase'),
                    ('b', 'open', 'controlled', 'low', 'high', 'decrease'),
                    ('c', 'open', 'open', 'low', 'high', 'confidence_only'),
                    ('d', 'controlled', 'controlled', 'high', 'high', 'unchanged')]
        records = []
        for sid, first, second, conf1, conf2, _ in fixtures:
            for config, level, conf in [('B1', first, conf1), ('B2', second, conf2)]:
                r = exp.base_record(sid, config, {'classifier_sha256': 'hash', 'python_version': 'test', 'pyyaml_version': 'test'})
                r.update(status='ok', classification=level, historical_label=first, manifest_sha256='same',
                         legacy_confidence_by_workload=[{'workload': 'Pod/demo/app', 'confidence': conf}],
                         result={'workloads': [{'entrypoints': [{'evidence': [config]}]}]})
                records.append(r)
        pairs = exp.pair_results(records)
        self.assertEqual([p['change_group'] for p in pairs], [f[-1] for f in fixtures])
        self.assertEqual(pairs[0]['historical_agreement_change'], 'lost')
        s = exp.summarize(records, pairs, {}, 0)
        self.assertEqual(s['category_changes'], exp.ratio(2, 4))
        self.assertEqual(s['change_groups'], {'increase': 1, 'decrease': 1, 'confidence_only': 1, 'unchanged': 1})
        records[1]['manifest_sha256'] = 'different'
        with self.assertRaises(ValueError):
            exp.pair_results(records)

    def test_export_roundtrip_preserves_complete_output_and_csv(self):
        self.scenario(cloud={'Nodes': [{}]})
        records, pairs, summary = exp.run_experiment(self.scenarios)
        output = self.root / 'export'
        exp.export_results(output, records, pairs, summary)
        self.assertEqual({p.name for p in output.iterdir()}, {
            'raw_results.json', 'paired_comparison.csv', 'summary.json', 'report.md'})
        raw = json.loads((output / 'raw_results.json').read_text())
        self.assertEqual(raw['executions'], records)
        self.assertIn('notes', raw['executions'][0]['result']['workloads'][0])
        self.assertIn('evidence', raw['executions'][0]['result']['workloads'][0]['entrypoints'][0])
        with (output / 'paired_comparison.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 1)
        self.assertEqual(json.loads(rows[0]['b1_legacy_confidence']), exp.confidence_map(records[0]))
        self.assertEqual(rows[0]['b1_manifest_sha256'], rows[0]['b2_manifest_sha256'])
        self.assertEqual(json.loads((output / 'summary.json').read_text()), summary)

    def test_no_silent_overwrite(self):
        self.scenario()
        output = self.root / 'export'
        self.assertEqual(self.run_cli(output), 0)
        before = {p.name: p.read_bytes() for p in output.iterdir()}
        self.assertEqual(self.run_cli(output), 1)
        self.assertEqual(before, {p.name: p.read_bytes() for p in output.iterdir()})

    def test_invalid_json_is_error_not_missing(self):
        path = self.scenario()
        (path / 'cloud.json').write_text('{invalid')
        records, pairs, summary = exp.run_experiment(self.scenarios)
        self.assertEqual(records[0]['status'], 'ok')
        self.assertEqual(records[1]['status'], 'error')
        self.assertEqual(records[1]['errors'][0]['phase'], 'snapshot')
        self.assertFalse(records[1]['classification_attempted'])
        self.assertEqual(pairs, [])
        self.assertEqual(summary['all_scenarios']['B2']['successful_executions'], 0)
        self.assertEqual(self.run_cli(self.root / 'bad-export'), 1)
        exported = json.loads((self.root / 'bad-export' / 'raw_results.json').read_text())
        self.assertEqual(exported['executions'][1]['status'], 'error')

    def test_invalid_cloud_shapes_rejected(self):
        for value in ([], {}, {'Nodes': 'wrong'}, {'Nodes': [1]},
                      {'SecurityGroups': [{}]}, {'LoadBalancers': [{'DNSName': 'local'}]},
                      {'SecurityGroups': [{'GroupId': 'sg', 'IpPermissions': [{'IpRanges': [0]}]}]}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                exp.validate_cloud(value)

    def test_invalid_yaml_records_both_errors(self):
        self.scenario(cloud={'Nodes': [{}]}, manifest='kind: [')
        records, pairs, summary = exp.run_experiment(self.scenarios)
        self.assertEqual([r['status'] for r in records], ['error', 'error'])
        self.assertEqual(pairs, [])
        self.assertEqual(len(summary['errors']), 2)
        self.assertEqual(self.run_cli(self.root / 'export'), 1)

    def test_no_workload_is_execution_error_not_category(self):
        self.scenario(manifest='apiVersion: v1\nkind: Service\nmetadata: {name: only-service}')
        records, _, _ = exp.run_experiment(self.scenarios)
        self.assertEqual(records[0]['status'], 'error')
        self.assertIsNone(records[0]['classification'])
        self.assertEqual(records[0]['result'], {'system_exposure': None, 'workloads': []})

    def test_missing_manifest_and_label_retained(self):
        path = self.scenario()
        (path / 'manifests.yaml').unlink()
        (path / 'expected.json').unlink()
        records, _, summary = exp.run_experiment(self.scenarios)
        self.assertEqual(records[0]['status'], 'error')
        self.assertEqual({e['phase'] for e in records[0]['errors']}, {'manifests', 'historical_label'})
        self.assertEqual(len(summary['errors']), 2)

    def test_bad_label_does_not_hide_classification_but_excludes_pair(self):
        self.scenario(cloud={'Nodes': [{}]}, expected='not-a-category')
        records, pairs, s = exp.run_experiment(self.scenarios)
        self.assertEqual(records[0]['classification'], 'open')
        self.assertEqual(records[0]['status'], 'error')
        self.assertEqual(pairs, [])
        self.assertEqual(s['all_scenarios']['B1']['historical_agreement']['denominator'], 0)

    def test_classification_exception_and_cli_nonzero(self):
        self.scenario(cloud={'Nodes': [{}]})
        with patch.object(exp, 'analyze', side_effect=RuntimeError('synthetic failure')):
            self.assertEqual(self.run_cli(self.root / 'export'), 1)
        s = json.loads((self.root / 'export' / 'summary.json').read_text())
        self.assertEqual(len(s['errors']), 2)
        self.assertEqual(s['eligible_pairs'], 0)

    def test_empty_discovery_nonzero_without_export(self):
        output = self.root / 'export'
        self.assertEqual(self.run_cli(output), 1)
        self.assertFalse(output.exists())

    def test_parser_objects_cannot_leak_mutation_between_modes(self):
        self.scenario(cloud={'Nodes': [{}]})
        observed = []
        original = exp.analyze

        def mutating(objects, cloud):
            observed.append(objects[0]['metadata']['name'])
            result = original(objects, cloud)
            objects[0]['metadata']['name'] = 'changed-by-mock'
            return result

        with patch.object(exp, 'analyze', side_effect=mutating):
            exp.run_experiment(self.scenarios)
        self.assertEqual(observed, ['app', 'app'])

    def test_changed_file_during_parse_rejected(self):
        path = self.scenario()
        original = exp.load_manifests

        def changing(manifest):
            result = original(manifest)
            manifest.write_text(MANIFEST + '\n# synthetic change')
            return result

        with patch.object(exp, 'load_manifests', side_effect=changing):
            records, _, _ = exp.run_experiment(self.scenarios)
        self.assertEqual(records[0]['status'], 'error')
        self.assertIn('mudou', records[0]['errors'][0]['message'])
        self.assertTrue(path.exists())

    def test_paths_outside_repository_rejected_before_read(self):
        with self.assertRaises(ValueError):
            exp.local_path(Path('/not-an-academic-input'))
        link = self.scenarios / '01-link'
        # Alvo sintético no mesmo diretório; não consulta nada fora do projeto.
        link.symlink_to(self.root / 'nonexistent-target')
        with self.assertRaises(ValueError):
            exp.local_path(link)

    def test_real_corpus_inventory_and_reproducible_categorical_results(self):
        first, pairs, s = exp.run_experiment()
        second, pairs2, s2 = exp.run_experiment()
        self.assertEqual(s['total_scenarios'], 16)
        self.assertEqual(s['b2_snapshot_files'], 10)
        self.assertEqual(s['eligible_pairs'], 10)
        self.assertEqual(s['all_scenarios']['B1']['successful_executions'], 16)
        self.assertEqual(s['all_scenarios']['B2']['successful_executions'], 10)
        self.assertEqual(len(s['non_applicable']), 6)
        self.assertEqual(s['errors'], [])
        self.assertEqual(pairs, pairs2)
        for a, b in zip(first, second):
            self.assertEqual(a['result'], b['result'])
            self.assertEqual(a['manifest_sha256'], b['manifest_sha256'])
        self.assertEqual(s['transition_b1_to_b2'], s2['transition_b1_to_b2'])

    def test_launcher_guard_denies_simulated_network_and_process_events(self):
        # Apenas eventos sintéticos de auditoria; não abre socket nem inicia processo.
        for event in ('socket.connect', 'subprocess.Popen'):
            with self.subTest(event=event), self.assertRaises(PermissionError):
                audit(event, (None,))

    def test_main_module_signals_nonzero_system_exit(self):
        import runpy
        self.scenario(cloud=[])
        with patch.object(sys, 'argv', [str(exp.ROOT / 'src' / 'run_experiments.py'),
                                      '--scenarios', str(self.scenarios),
                                      '--output', str(self.root / 'export')]), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
                self.assertRaises(SystemExit) as raised:
            runpy.run_path(str(exp.ROOT / 'src' / 'run_experiments.py'), run_name='__main__')
        self.assertEqual(raised.exception.code, 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
