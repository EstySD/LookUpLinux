"""Read-only real archive acceptance; use an isolated dictionary directory."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lookup import dicts, doctor, translate
from lookup.config import Config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = {'archive_sha256': hashlib.sha256(args.archive.read_bytes()).hexdigest(), 'checks': {}}
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        target = root / args.archive.name
        shutil.copyfile(args.archive, target)
        started = time.perf_counter()
        with dicts.open_all(config=Config(), roots=[root]) as dictionaries:
            report['open_seconds'] = time.perf_counter() - started
            assert not dictionaries.problems, dictionaries.problems
            report['entries'] = dictionaries.info()[0].entries
            for word, expected in [('cat', 'кот'), ('dog', 'собак'), ('hello', 'привет'), ('hallo', 'привет')]:
                result = translate.lookup(word, dictset=dictionaries, online=False, save=False)
                assert result.articles and any(expected in a.text.casefold() for a in result.articles), word
                report['checks'][word] = True
        with dicts.open_all(config=Config(), roots=[root]) as dictionaries:
            assert dictionaries.find('cat')
            report['checks']['reopen'] = True
        diagnostic = doctor._probe(target, 'yomitan')
        assert diagnostic['entries'] == report['entries']
        report['checks']['doctor'] = True
    report['source_hashes'] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(Path('lookup').glob('*.py'))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding='utf-8')
    print(json.dumps({'entries': report['entries'], 'seconds': report['open_seconds'], 'checks': report['checks']}))


if __name__ == '__main__':
    main()
