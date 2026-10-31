"""Measure real OCR against unchanged public fixture expectations; no skip mode."""
import argparse
import itertools
import json
import platform
from pathlib import Path
import statistics
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lookup import ocr
from lookup.normalize import normalize


def evaluate(root, images, psm, enlarge, invert):
    cases = []
    for image in images:
        for case in image['cases']:
            try:
                result = ocr.recognize_image(root/image['path'], case['point'],
                                             psm=psm, enlarge=enlarge, invert=invert,fallback=False)
                found = result.selection
                word = found.word if found else None
                tokens = [normalize(w) for w in found.line.split()] if found else []
                expected_tokens = [normalize(w) for w in case['line_tokens']]
                line_ok = tokens == expected_tokens
                compound_ok = not case['compound'] or (found and found.candidates and
                                                       found.candidates[0] == case['compound'])
                passed = word == case['word'] and line_ok and bool(compound_ok)
                cases.append({'image': image['path'], 'case': case['name'], 'expected': case['word'],
                              'actual': word, 'line': found.line if found else None,
                              'candidates': found.candidates if found else [], 'line_ok': line_ok,
                              'passed': passed, 'ms': result.timings['total']})
            except ocr.OcrError as error:
                cases.append({'image': image['path'], 'case': case['name'], 'passed': False,
                              'error': error.reason, 'ms': 0})
    return {'psm': psm, 'enlarge': enlarge, 'invert': invert,
            'passed': sum(c['passed'] for c in cases), 'total': len(cases),
            'median_ms': statistics.median(c['ms'] for c in cases), 'cases': cases}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--matrix', action='store_true')
    mode.add_argument('--check', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    manifest = json.loads((args.fixtures/'manifest.json').read_text(encoding='utf-8'))
    if len(manifest['images']) != 16 or manifest['style'].lower() != 'breeze':
        raise SystemExit('incomplete Breeze fixture set')
    version = subprocess.run(['tesseract', '--version'], capture_output=True, text=True,
                              timeout=5, check=True).stdout.splitlines()[0]
    settings = itertools.product((6, 11), (1, 2), ('never', 'auto')) if args.matrix else [
        (ocr.DEFAULT_PSM, ocr.DEFAULT_ENLARGE, ocr.DEFAULT_INVERT)]
    results = []
    for psm, enlarge, invert in settings:
        result = evaluate(args.fixtures, manifest['images'], psm, enlarge, invert)
        results.append(result)
        print(f'psm={psm} enlarge={enlarge} invert={invert}: '
              f'{result["passed"]}/{result["total"]}, median={result["median_ms"]:.1f}ms', flush=True)
    passing = [r for r in results if r['passed'] == r['total']]
    chosen = min(passing, key=lambda r: r['median_ms']) if passing else None
    report = {'python': platform.python_version(), 'platform': platform.platform(),
              'tesseract': version, 'origin': manifest['provenance'],
              'settings': results, 'chosen': {k: chosen[k] for k in ('psm', 'enlarge', 'invert', 'median_ms')}
              if chosen else None}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    if not passing:
        best = max(results, key=lambda r: r['passed'])
        for case in best['cases']:
            if not case['passed']:
                print(json.dumps(case, ensure_ascii=False))
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
