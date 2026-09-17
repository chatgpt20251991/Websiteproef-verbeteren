"""Offline tests of the exact embedded workflow code. No real API key or network.

Run: python -m unittest discover -s mulder-proef -v
Requires PyYAML (test dependency only).
"""
import base64
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import struct
import tempfile
import types
import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import zlib
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / '.github/workflows/avenzo-mulder-mockups.yml'
DOC = yaml.load(WORKFLOW.read_text(encoding='utf-8'), Loader=yaml.BaseLoader)
STEP = DOC['jobs']['mulder-proef']['steps'][1]
SCRIPT = STEP['run']
CODE = SCRIPT.split("python3 - <<'PYTHON'\n", 1)[1].rsplit('\nPYTHON', 1)[0]
g = types.ModuleType('mulder_workflow')
exec(compile(CODE, str(WORKFLOW), 'exec'), g.__dict__)
REFERENCE = (ROOT / 'mulder-referentie.png').read_bytes()
DUMMY = 'offline-test-placeholder-not-a-real-key'


def png(width, height):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data) & 0xffffffff)
    # Valid compressed grayscale PNG, created only as an offline test fixture.
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 0, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress((b'\0' * (width + 1)) * height)) + chunk(b'IEND', b''))


class WorkflowTests(unittest.TestCase):
    def invoke(self, mode='Controle', consent='false', key=DUMMY, ref=REFERENCE,
               resolution='4K', event='workflow_dispatch', attempt='1', response=None):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / g.REFERENCE_NAME).write_bytes(ref)
            env = {'RUNNER_TEMP': tmp, 'MOCKUP_TAAK': mode, 'MOCKUP_RESOLUTIE': resolution,
                   'MOCKUP_KWALITEIT': 'max', 'API_KOSTEN_AKKOORD': consent,
                   'OPENAI_API_KEY': key, 'GITHUB_EVENT_NAME': event, 'GITHUB_RUN_ATTEMPT': attempt,
                   'GITHUB_STEP_SUMMARY': str(root / 'summary.md')}
            def success(_key, fields, reference):
                self.assertEqual(reference, REFERENCE)
                self.assertEqual(fields['n'], '1')
                self.assertEqual(fields['model'], 'gpt-image-2.5-sunburst')
                self.assertEqual(fields['output_format'], 'png')
                return png(*map(int, fields['size'].split('x'))), {'usage': {'output_tokens': 10}}
            log = io.StringIO()
            # Every possible live network connection is denied, even if mocking changes.
            with contextlib.chdir(tmp), patch.dict(os.environ, env, clear=True), \
                    patch.object(socket.socket, 'connect', side_effect=AssertionError('Network forbidden')), \
                    patch.object(g, 'request_image', side_effect=response or success) as api, \
                    contextlib.redirect_stdout(log):
                code = g.run()
            out = root / 'mulder-mockup-resultaat'
            files = {p.name: p.read_bytes() for p in out.iterdir()}
            self.assertNotIn(DUMMY, log.getvalue())
            self.assertNotIn(DUMMY.encode(), b''.join(files.values()))
            self.assertTrue((root / 'summary.md').is_file())
            return code, json.loads(files['run-report.json']), api.call_count, files

    def test_yaml_and_safe_automatic_control(self):
        triggers = DOC['on']
        self.assertEqual(set(triggers), {'push', 'workflow_dispatch'})
        self.assertEqual(triggers['push']['branches'], ['codex/mulder-mockup-proef'])
        self.assertEqual(triggers['push']['paths'], ['.github/workflows/avenzo-mulder-mockups.yml', 'mulder-referentie.png'])
        inputs = triggers['workflow_dispatch']['inputs']
        self.assertEqual(inputs['taak']['default'], 'Controle')
        self.assertEqual(inputs['api_kosten_akkoord']['default'], 'false')
        self.assertEqual(DOC['permissions'], {'contents': 'read'})
        self.assertEqual(STEP['env']['OPENAI_API_KEY'], '${{ secrets.AVIN2 }}')
        self.assertIn("inputs.taak || 'Controle'", STEP['env']['MOCKUP_TAAK'])
        self.assertEqual(DOC['jobs']['mulder-proef']['steps'][2]['with']['path'], '${{ runner.temp }}/mulder-mockup-resultaat/')

    def test_reference_hash_and_dimensions(self):
        self.assertEqual(hashlib.sha256(REFERENCE).hexdigest(), g.REFERENCE_SHA256)
        self.assertEqual(g.png_dimensions(REFERENCE), (1536, 1024))

    def test_control_zero_requests_and_both_prompts(self):
        code, report, count, files = self.invoke(event='push')
        self.assertEqual((code, count, report['status']), (0, 0, 'local_checks_passed'))
        self.assertEqual(len(report['prepared_requests']), 2)
        self.assertIn('opdracht-desktop.txt', files)
        self.assertIn('opdracht-mobiel.txt', files)

    def test_cost_gate(self):
        for consent in ['false', '', 'True', '1']:
            with self.subTest(consent=consent):
                code, report, count, _ = self.invoke('Desktop en mobiel', consent)
                self.assertEqual((code, count, report['requests_submitted']), (1, 0, 0))

    def test_no_generation_on_push_even_with_consent(self):
        self.assertEqual(self.invoke('Desktop en mobiel', 'true', event='push')[:3:2], (1, 0))

    def test_paid_rerun_blocked(self):
        for attempt in ['2', '3', '', 'invalid']:
            with self.subTest(attempt=attempt):
                code, _, count, _ = self.invoke('Desktop en mobiel', 'true', attempt=attempt)
                self.assertEqual((code, count), (1, 0))

    def test_missing_secret(self):
        code, report, count, _ = self.invoke(key='')
        self.assertEqual((code, count, report['secret_present']), (1, 0, False))

    def test_wrong_reference(self):
        code, _, count, _ = self.invoke(ref=b'wrong reference')
        self.assertEqual((code, count), (1, 0))

    def test_two_separate_original_images(self):
        code, report, count, files = self.invoke('Desktop en mobiel', 'true')
        self.assertEqual((code, count, report['requests_submitted']), (0, 2, 2))
        self.assertEqual(files['mulder-desktop.png'], png(3840, 2160))
        self.assertEqual(files['mulder-mobiel.png'], png(1728, 3840))

    def test_qhd_and_single_view(self):
        code, _, count, files = self.invoke('Mobiel', 'true', resolution='QHD')
        self.assertEqual((code, count), (0, 1))
        self.assertEqual(g.png_dimensions(files['mulder-mobiel.png']), (1152, 2560))
        self.assertNotIn('mulder-desktop.png', files)

    def test_failure_stops_second_request(self):
        code, report, count, _ = self.invoke('Desktop en mobiel', 'true', response=g.SafeFailure('Safe failure'))
        self.assertEqual((code, count, report['requests_submitted']), (1, 1, 1))

    def test_dimension_mismatch_saved_and_stops(self):
        code, report, count, files = self.invoke('Desktop en mobiel', 'true', response=lambda *args: (png(16, 16), {}))
        self.assertEqual((code, count), (1, 1))
        self.assertIn('mulder-desktop-afwijkende-resolutie.png', files)
        self.assertEqual(report['results'][0]['status'], 'dimension_mismatch')

    def test_unexpected_error_redacted(self):
        code, _, count, _ = self.invoke('Desktop en mobiel', 'true', response=RuntimeError(DUMMY))
        self.assertEqual((code, count), (1, 1))

    def test_size_constraints(self):
        for sizes in g.SIZES.values():
            for size in sizes.values():
                self.assertEqual(g.validate_size(size), tuple(map(int, size.split('x'))))
        for size in ['0x0', '3841x2160', '3840x3840', '1024x4096', '16x16', 'auto']:
            with self.subTest(size=size), self.assertRaises(g.SafeFailure):
                g.validate_size(size)

    def test_png_corruption_rejected(self):
        for data in [b'wrong', REFERENCE[:-1], REFERENCE[:60] + b'X' + REFERENCE[61:]]:
            with self.assertRaises(g.SafeFailure):
                g.png_dimensions(data)

    def test_multipart_reference_and_no_secret(self):
        body, content_type = g.make_multipart({'model': g.MODEL, 'n': '1'}, REFERENCE)
        self.assertIn(REFERENCE, body)
        self.assertIn(b'name="image[]"', body)
        self.assertIn('multipart/form-data', content_type)
        self.assertNotIn(DUMMY.encode(), body)

    def test_redirect_rejected(self):
        with self.assertRaises(g.SafeFailure):
            g.NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.com')

    def test_usage_redacts_strings(self):
        self.assertEqual(g.numeric_usage({'input_tokens': 1, 'text': DUMMY, 'nested': {'output_tokens': 3}}),
                         {'input_tokens': 1, 'nested': {'output_tokens': 3}})

    def test_transport_no_retries_and_safe_errors(self):
        for error in [urllib.error.HTTPError(g.ENDPOINT, 401, DUMMY, {}, None),
                      urllib.error.HTTPError(g.ENDPOINT, 429, DUMMY, {}, None),
                      urllib.error.HTTPError(g.ENDPOINT, 500, DUMMY, {}, None),
                      TimeoutError(DUMMY), urllib.error.URLError(DUMMY)]:
            opener = MagicMock()
            opener.open.side_effect = error
            with patch.object(g.urllib.request, 'build_opener', return_value=opener):
                with self.assertRaises(g.SafeFailure) as caught:
                    g.request_image(DUMMY, {'n': '1'}, REFERENCE)
            self.assertNotIn(DUMMY, str(caught.exception))
            self.assertEqual(opener.open.call_count, 1)

    def test_transport_official_endpoint_and_response(self):
        sample = png(16, 16)
        response = MagicMock()
        response.read.return_value = json.dumps({'data': [{'b64_json': base64.b64encode(sample).decode()}],
                                                'usage': {'output_tokens': 7}}).encode()
        response.headers = {'x-request-id': 'req_offline_fixture'}
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value = response
        with patch.object(g.urllib.request, 'build_opener', return_value=opener):
            image, metadata = g.request_image(DUMMY, {'n': '1'}, REFERENCE)
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, 'https://api.openai.com/v1/images/edits')
        self.assertEqual(request.get_method(), 'POST')
        self.assertEqual(image, sample)
        self.assertEqual(metadata['usage'], {'output_tokens': 7})
        self.assertEqual(opener.open.call_count, 1)


if __name__ == '__main__':
    unittest.main()

