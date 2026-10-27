"""Occurrence-specific translation uses public captured responses, never live requests."""
from dataclasses import replace
import json
from pathlib import Path
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlsplit

from lookup import context, online


def request(text='They sat on the bank of the river.', selected='bank'):
    start = text.index(selected)
    return context.ContextRequest(text, start, start+len(selected), selected)


def body(text):
    return json.dumps([[[text, 'source']], None, 'en']).encode()


class ProviderTests(unittest.TestCase):
    def translated(self, req, response):
        with mock.patch.object(online, '_fetch', return_value=response) as fetch:
            value = context.translate_context(req)
        return value, fetch

    def test_captured_live_occurrences_and_phrase(self):
        path = Path(__file__).parents[1]/'.planning/phases/05.1-context/provider-probes.json'
        probes = json.loads(path.read_text(encoding='utf-8'))
        meanings = {}
        for probe in probes:
            if not probe['endpoint'].endswith('/single') or probe['case'] in ('escaped-source','no-span-control'):
                continue
            with self.subTest(case=probe['case']):
                marked = probe['params']['q']
                start, end = marked.index('<b>'), marked.index('</b>')-3
                source = marked.replace('<b>', '').replace('</b>', '')
                req = context.ContextRequest(source, start, end, source[start:end])
                value, _ = self.translated(req, probe['body'].encode())
                self.assertEqual(value.meaning, probe['extracted'][0])
                meanings[probe['case']] = value.meaning
        self.assertEqual(len(meanings), 8)
        self.assertNotEqual(meanings['river'], meanings['finance'])
        self.assertNotEqual(meanings['repeat-river'], meanings['repeat-finance'])

    def test_exact_text_is_escaped_and_only_selected_occurrence_marked(self):
        source = 'The bank & the bank\nby the river.'
        start = source.rindex('bank')
        req = context.ContextRequest(source, start, start+4, 'bank')
        value, fetch = self.translated(req, body('Банк и <b>берег</b> реки.'))
        query = parse_qs(urlsplit(fetch.call_args.args[0]).query)
        self.assertEqual(query['q'], ['The bank &amp; the <b>bank</b>\nby the river.'])
        self.assertEqual(query['client'], ['gtx'])
        self.assertEqual(query['dt'], ['t'])
        self.assertEqual(value.provider, req.provider)
        self.assertEqual(fetch.call_args.args[-1], online.GOOGLE_HOST)
        self.assertLessEqual(fetch.call_args.args[1], online.DEADLINE_S)

    def test_invalid_source_is_refused_before_network(self):
        valid = request()
        invalid = [dict(start=True), dict(end=False), dict(start=-1), dict(end=1000),
                   dict(start=20,end=20),dict(word='river'),dict(context='x'*501),
                   dict(context='They <b>sat</b> on the bank.'),
                   dict(context='They sat\x00 on the bank.'),dict(context=None),
                   dict(word=''),dict(provider=''),dict(target='')]
        with mock.patch.object(online, '_fetch') as fetch:
            for fields in invalid:
                with self.subTest(fields=fields):
                    with self.assertRaises(online.TranslateError) as raised:
                        replace(valid, **fields)
                    self.assertEqual(str(raised.exception), 'bad_response')
            fetch.assert_not_called()

    def test_malformed_or_unsuitable_spans_are_private_errors(self):
        invalid = ['Перевод без метки.', '<b>берег</b><b>банк</b>', '<b>берег',
                   'берег</b>', '<b><b>берег</b></b>', '<b class="x">берег</b>',
                   '<B>берег</B>', '<b>берег</b><!-- x -->', '<!DOCTYPE x><b>берег</b>',
                   '<b/>берег', '<b></b>', '<b>bank</b>', '<b>shore</b>',
                   '<b>берег\x00</b>', '<b>берег &lt;img&gt;</b>',
                   '<b>'+('я'*201)+'</b>', '<b>берег</b>'+('я'*5000),
                   '<b>bank берег</b>', '<b>берег</b><?pi x?>']
        for response in invalid:
            with self.subTest(response=response[:35]):
                with self.assertRaises(online.TranslateError) as raised:
                    self.translated(request(), body(response))
                self.assertEqual(str(raised.exception), 'bad_response')

    def test_bad_json_shapes_and_oversized_body(self):
        for response in (b'not json', b'{}', b'[]', b'[[null]]', b'[[[1]]]',
                         b'[[[]]]', b'x'*(context.MAX_BODY+1)):
            with self.subTest(response=response[:20]):
                with self.assertRaises(online.TranslateError):
                    self.translated(request(), response)

    def test_transport_reasons_pass_without_source_details(self):
        for reason in online.REASONS:
            with mock.patch.object(online, '_fetch', side_effect=online.TranslateError(reason)):
                with self.assertRaises(online.TranslateError) as raised:
                    context.translate_context(request())
                self.assertEqual(str(raised.exception), reason)

    def test_unsupported_method_or_target_never_uses_network(self):
        with mock.patch.object(online, '_fetch') as fetch:
            for fields in (dict(provider='other-v1'),dict(target='en')):
                with self.assertRaises(online.TranslateError):
                    context.translate_context(replace(request(), **fields))
            fetch.assert_not_called()
