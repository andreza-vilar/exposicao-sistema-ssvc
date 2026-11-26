"""Seleção e agregação CP02.1; não valida cientificamente categorias SSVC."""
from contextlib import redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

import exposure_analyzer as legacy
import exposure_analyzer_v2 as v2

FIXTURES = v2.ROOT / 'tests' / 'fixtures' / 'cp02.1'


def workload(name='single', namespace='demo', kind='Deployment'):
    return {'kind': kind, 'metadata': {'name': name, 'namespace': namespace},
            'spec': {'template': {'metadata': {'labels': {'app': name}},
                                  'spec': {'containers': []}}}}


class UnitSelectionTests(unittest.TestCase):
    def setUp(self):
        self.objects = legacy.load_manifests(FIXTURES / 'multi-workload.yaml')
        self.temporary = tempfile.TemporaryDirectory(prefix='cp02_1_', dir=Path(__file__).parent)
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def target(self, target, objects=None):
        return v2.analyze_units(self.objects if objects is None else objects, mode='target', target=target)

    def test_single_workload(self):
        objects = [workload()]
        system = v2.analyze_units(objects)
        target = self.target('Deployment/demo/single', objects)
        self.assertEqual(system['status'], 'ok')
        self.assertEqual(system['selected_exposure'], target['selected_exposure'])
        self.assertEqual(target['selected_result'], system['global_result']['workloads'][0])

    def test_multiple_workloads_and_explicit_system_strategy(self):
        result = v2.analyze_units(self.objects)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['selected_exposure'], 'open')
        self.assertEqual(result['global_exposure'], 'open')
        self.assertEqual({w['exposure'] for w in result['global_result']['workloads']}, {'small', 'controlled', 'open'})
        self.assertEqual(result['aggregation']['global_strategy'], 'legacy_ordinal_maximum')
        self.assertFalse(result['aggregation']['normative_system_boundary_assumed'])
        self.assertIsNone(result['selected_legacy_confidence'])

    def test_select_open(self):
        result = self.target('Deployment/demo/frontend')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['selected_exposure'], 'open')
        self.assertEqual(result['selected_legacy_confidence'], 'medium')
        self.assertTrue(result['selected_result']['entrypoints'])

    def test_select_controlled_does_not_inherit_open_global(self):
        result = self.target('Deployment/demo/backend')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['selected_exposure'], 'controlled')
        self.assertEqual(result['global_exposure'], 'open')
        self.assertEqual(result['selected_unit']['identifier'], 'Deployment/demo/backend')

    def test_select_small_keeps_evidence_and_notes(self):
        result = self.target('Deployment/demo/worker')
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['selected_exposure'], 'small')
        self.assertEqual(result['global_exposure'], 'open')
        expected = next(w for w in result['global_result']['workloads'] if w['workload'] == 'Deployment/demo/worker')
        self.assertEqual(result['selected_result'], expected)
        self.assertIn('NetworkPolicy', ' '.join(expected['entrypoints'][0]['evidence']))
        self.assertIn('notes', result['selected_result'])

    def test_unknown_target_is_error_with_global_context_not_substitution(self):
        result = self.target('Deployment/demo/missing')
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['errors'][0]['code'], 'target_not_found')
        self.assertIsNone(result['selected_exposure'])
        self.assertIsNone(result['selected_result'])
        self.assertIsNone(result['selected_legacy_confidence'])
        self.assertEqual(result['global_exposure'], 'open')
        self.assertEqual(len(result['workloads_found']), 3)

    def test_full_identifier_required(self):
        for target in (None, '', 'backend', 'demo/backend', 'Deployment//backend',
                       'Deployment/demo/backend/extra', ' Deployment/demo/backend'):
            with self.subTest(target=target):
                result = self.target(target)
                self.assertEqual(result['status'], 'error')
                self.assertEqual(result['errors'][0]['code'], 'invalid_target_identifier')
                self.assertIsNone(result['selected_exposure'])

    def test_same_name_different_namespaces(self):
        objects = [workload('same', 'alpha'), workload('same', 'beta')]
        for namespace in ('alpha', 'beta'):
            target = 'Deployment/%s/same' % namespace
            with self.subTest(target=target):
                result = self.target(target, objects)
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(result['selected_result']['workload'], target)
                self.assertEqual(len(result['workloads_found']), 2)

    def test_same_name_different_kinds(self):
        objects = [workload('same', kind='Deployment'), workload('same', kind='StatefulSet')]
        for kind in ('Deployment', 'StatefulSet'):
            target = kind + '/demo/same'
            with self.subTest(target=target):
                result = self.target(target, objects)
                self.assertEqual(result['status'], 'ok')
                self.assertEqual(result['selected_result']['workload'], target)

    def test_namespace_omitted_uses_default(self):
        obj = workload()
        del obj['metadata']['namespace']
        result = self.target('Deployment/default/single', [obj])
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['workloads_found'], ['Deployment/default/single'])

    def test_no_supported_workloads(self):
        for objects in ([], [{'kind': 'Service', 'metadata': {'name': 'svc'}}], [workload(kind='Job')]):
            with self.subTest(objects=objects):
                result = v2.analyze_units(objects)
                self.assertEqual(result['errors'][0]['code'], 'no_supported_workloads')
                self.assertIsNone(result['selected_exposure'])
                self.assertIsNone(result['global_exposure'])

    def test_duplicate_target_is_ambiguous_before_legacy_analysis(self):
        objects = [workload('same'), workload('same')]
        with patch.object(legacy, 'analyze', side_effect=AssertionError('Não deve executar')) as analyze:
            result = self.target('Deployment/demo/same', objects)
        self.assertFalse(analyze.called)
        self.assertEqual(result['errors'][0]['code'], 'ambiguous_target')
        self.assertEqual(result['errors'][0]['details']['duplicates'], {'Deployment/demo/same': 2})
        self.assertIsNone(result['selected_exposure'])
        self.assertIsNone(result['global_result'])

    def test_duplicates_in_system_or_other_target_reject_whole_input(self):
        objects = [workload('same'), workload('same'), workload('unique')]
        for mode, target in (('system', None), ('target', 'Deployment/demo/unique')):
            result = v2.analyze_units(objects, mode=mode, target=target)
            self.assertEqual(result['errors'][0]['code'], 'duplicate_workload_identities')
            self.assertIsNone(result['global_exposure'])
            self.assertIsNone(result['selected_exposure'])

    def test_snapshot_changes_only_legacy_inputs_and_confidence(self):
        without = v2.analyze_files(FIXTURES / 'multi-workload.yaml', mode='target', target='Deployment/demo/frontend')
        with_cloud = v2.analyze_files(FIXTURES / 'multi-workload.yaml', FIXTURES / 'cloud.json',
                                     mode='target', target='Deployment/demo/frontend')
        self.assertEqual(with_cloud['status'], 'ok')
        self.assertEqual(without['selected_exposure'], with_cloud['selected_exposure'])
        self.assertEqual(without['selected_legacy_confidence'], 'medium')
        self.assertEqual(with_cloud['selected_legacy_confidence'], 'high')
        self.assertEqual(with_cloud['inputs']['snapshot']['origin'], 'synthetic')
        self.assertEqual(without['inputs']['manifests'], with_cloud['inputs']['manifests'])
        cloud = legacy.Cloud(json.loads((FIXTURES / 'cloud.json').read_text()))
        self.assertEqual(with_cloud['global_result'], legacy.analyze(self.objects, cloud))

    def test_analyze_called_once_with_all_resources_and_no_mutation(self):
        before = deepcopy(self.objects)
        with patch.object(legacy, 'analyze', wraps=legacy.analyze) as analyze:
            result = self.target('Deployment/demo/backend')
        self.assertEqual(analyze.call_count, 1)
        self.assertEqual(analyze.call_args.args[0], self.objects)
        self.assertEqual(self.objects, before)
        self.assertEqual(result['global_result'], legacy.analyze(self.objects))

    def test_determinism_and_json_versioned_contract(self):
        a = self.target('Deployment/demo/backend')
        self.assertEqual(a, self.target('Deployment/demo/backend'))
        self.assertEqual(json.loads(json.dumps(a)), a)
        self.assertEqual(a['schema_version'], '1.0.0')
        self.assertEqual(len(a['classifier']['sha256']), 64)
        self.assertEqual(len(a['classifier']['adapter_sha256']), 64)
        self.assertEqual(a['aggregation']['selected_strategy'], 'exact_workload_lookup')
        self.assertTrue(a['limitations'])

    def test_mode_validation(self):
        for mode, target, expected in [('other', None, 'invalid_mode'),
                                       ('system', 'Deployment/demo/backend', 'unexpected_target')]:
            result = v2.analyze_units(self.objects, mode=mode, target=target)
            self.assertEqual(result['status'], 'error')
            self.assertEqual(result['errors'][0]['code'], expected)
            self.assertIsNone(result['selected_exposure'])

    def test_invalid_objects_and_missing_workload_identity(self):
        for objects, expected in [([1], 'invalid_objects'),
                                   ({}, 'invalid_objects'),
                                   ([{'kind': 'Pod', 'metadata': {}}], 'invalid_workload_identity'),
                                   ([workload(namespace='')], 'invalid_workload_identity'),
                                   ([workload(name='bad/name')], 'invalid_workload_identity')]:
            with self.subTest(expected=expected, objects=objects):
                result = v2.analyze_units(objects)
                self.assertEqual(result['errors'][0]['code'], expected)
                self.assertIsNone(result['selected_exposure'])

    def test_all_historical_results_equal_in_b1_and_b2(self):
        for directory in sorted((v2.ROOT / 'scenarios').iterdir()):
            objects = legacy.load_manifests(directory / 'manifests.yaml')
            clouds = [None]
            if (directory / 'cloud.json').exists():
                clouds.append(legacy.Cloud(json.loads((directory / 'cloud.json').read_text())))
            for cloud in clouds:
                with self.subTest(scenario=directory.name, cloud=cloud is not None):
                    expected = legacy.analyze(objects, cloud)
                    result = v2.analyze_units(objects, cloud)
                    self.assertEqual(result['status'], 'ok')
                    self.assertEqual(result['global_result'], expected)
                    self.assertEqual(result['global_exposure'], expected['system_exposure'])
                    target = v2.analyze_units(objects, cloud, mode='target', target='Deployment/demo/app')
                    self.assertEqual(target['status'], 'ok')
                    self.assertEqual(target['selected_result'], expected['workloads'][0])

    def test_manifest_directory_and_kind_list(self):
        payload = {'apiVersion': 'v1', 'kind': 'List', 'items': [workload()]}
        (self.directory / 'single.yaml').write_text(json.dumps(payload))  # JSON é YAML válido.
        result = v2.analyze_files(self.directory)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['workloads_found'], ['Deployment/demo/single'])
        self.assertEqual(len(result['inputs']['manifests']), 1)

    def test_invalid_files_or_snapshot_return_structured_errors(self):
        broken = self.directory / 'bad.yaml'
        broken.write_text('kind: [')
        result = v2.analyze_files(broken)
        self.assertEqual(result['status'], 'error')
        self.assertEqual(result['errors'][0]['code'], 'input_error')
        self.assertIsNone(result['selected_exposure'])
        cloud = self.directory / 'bad.json'
        cloud.write_text('[]')
        result = v2.analyze_files(FIXTURES / 'multi-workload.yaml', cloud)
        self.assertEqual(result['status'], 'error')
        result = v2.analyze_files(self.directory / 'missing.yaml')
        self.assertEqual(result['errors'][0]['code'], 'manifest_path_not_found')

    def test_empty_directory(self):
        result = v2.analyze_files(self.directory)
        self.assertEqual(result['errors'][0]['code'], 'no_manifest_files')

    def test_rejects_external_and_symlink_paths_before_loading(self):
        link = self.directory / 'link.yaml'
        link.symlink_to(self.directory / 'nonexistent-local-file')
        for path in (link, self.directory, Path('/not-an-academic-input')):
            with self.subTest(path=path), patch.object(legacy, 'load_manifests') as loader:
                result = v2.analyze_files(path)
                self.assertEqual(result['status'], 'error')
                self.assertFalse(loader.called)

    def test_error_from_legacy_never_uses_global_as_selected_fallback(self):
        with patch.object(legacy, 'analyze', side_effect=ValueError('synthetic failure')):
            result = self.target('Deployment/demo/backend')
        self.assertEqual(result['errors'][0]['code'], 'legacy_analysis_error')
        self.assertIsNone(result['selected_exposure'])

    def test_cli_json_and_text(self):
        args = ['--manifests', str(FIXTURES / 'multi-workload.yaml'), '--mode', 'target',
                '--target', 'Deployment/demo/backend']
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = v2.main(args + ['--format', 'json'])
        self.assertEqual(code, 0)
        result = json.loads(stream.getvalue())
        self.assertEqual(result['selected_exposure'], 'controlled')
        stream = io.StringIO()
        with redirect_stdout(stream):
            code = v2.main(args + ['--format', 'text'])
        self.assertEqual(code, 0)
        self.assertIn('EXPOSIÇÃO SELECIONADA: controlled', stream.getvalue())
        self.assertIn('EXPOSIÇÃO GLOBAL (contexto): open', stream.getvalue())

    def test_cli_main_module_nonzero_json_error(self):
        stream = io.StringIO()
        argv = [str(v2.ROOT / 'src' / 'exposure_analyzer_v2.py'), '--manifests', str(FIXTURES / 'multi-workload.yaml'),
                '--mode', 'target', '--target', 'Deployment/demo/missing', '--format', 'json']
        with patch.object(sys, 'argv', argv), redirect_stdout(stream), self.assertRaises(SystemExit) as raised:
            runpy.run_path(argv[0], run_name='__main__')
        self.assertEqual(raised.exception.code, 1)
        result = json.loads(stream.getvalue())
        self.assertEqual(result['status'], 'error')
        self.assertIsNone(result['selected_exposure'])
        self.assertEqual(result['global_exposure'], 'open')


if __name__ == '__main__':
    unittest.main(verbosity=2)
