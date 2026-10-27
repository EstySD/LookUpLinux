"""Research-only bounded public synthetic probes; no credentials or user text."""
import concurrent.futures
import json
import html
from html.parser import HTMLParser
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

CASES = [
    ('river', 'They sat on the <b>bank</b> of the river.'),
    ('finance', 'She deposited her money in the <b>bank</b>.'),
    ('repeat-river', 'The <b>bank</b> of the river is next to the bank that holds my savings.'),
    ('repeat-finance', 'The bank of the river is next to the <b>bank</b> that holds my savings.'),
    ('two-sentences-river', 'The bank approved the loan. They waited on the <b>bank</b> of the river.'),
    ('two-sentences-finance', 'The <b>bank</b> approved the loan. They waited on the bank of the river.'),
    ('multiline-river', 'They sat on the <b>bank</b>\nof the river and watched\nthe ducks swim past.'),
    ('selected-phrase', 'The prisoners managed to <b>break out</b> of jail.'),
    ('escaped-source', 'The sign said &lt;b&gt; before they sat on the <b>bank</b> of the river.'),
    ('no-span-control', 'They sat on the bank of the river.'),
]


class Span(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.spans = []
        self.active = False
        self.invalid = False

    def handle_starttag(self, tag, attrs):
        if tag != 'b' or attrs or self.active:
            self.invalid = True
        self.active = True
        self.parts = []

    def handle_endtag(self, tag):
        if tag != 'b' or not self.active:
            self.invalid = True
        self.spans.append(''.join(self.parts))
        self.active = False

    def handle_data(self, text):
        if self.active:
            self.parts.append(text)


def probe(item):
    name, text, endpoint, params = item
    url = endpoint + '?' + urllib.parse.urlencode(dict(params, q=text))
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    started = time.monotonic()
    result = {'case': name, 'endpoint': endpoint, 'params': dict(params, q=text)}
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            result.update(status=response.status, body=response.read(131072).decode('utf-8', 'replace'))
        if endpoint.endswith('/single'):
            payload = json.loads(result['body'])
            translated = ''.join(segment[0] for segment in payload[0] if isinstance(segment[0], str))
            span = Span()
            span.feed(translated)
            result.update(translated=translated, extracted=span.spans,
                          valid_span=not span.invalid and not span.active and len(span.spans) == 1)
    except urllib.error.HTTPError as error:
        result.update(status=error.code, body=error.read(2000).decode('utf-8', 'replace'))
    except Exception as error:
        result.update(error=type(error).__name__)
    result['elapsed_ms'] = round((time.monotonic() - started) * 1000, 1)
    return result


def main():
    endpoints = [
        ('https://translate.googleapis.com/translate_a/t', {'client': 'te', 'format': 'html', 'v': '1.0', 'sl': 'en', 'tl': 'ru'}),
        ('https://translate.googleapis.com/translate_a/single', {'client': 'gtx', 'dt': 't', 'sl': 'en', 'tl': 'ru'}),
    ]
    inputs = [(name, text, endpoint, params) for endpoint, params in endpoints for name, text in CASES]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(probe, inputs))
    Path(__file__).with_name('provider-probes.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    for result in results:
        print(json.dumps({key: result.get(key) for key in ('case', 'endpoint', 'status', 'extracted', 'valid_span', 'error')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
