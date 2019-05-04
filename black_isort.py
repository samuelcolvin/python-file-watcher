#!/home/samuel/code/file-watchers/env/bin/python
import json
import re
import subprocess
import sys
from pathlib import Path

from isort.main import main as isort_main

trailing_white = re.compile(b' +\n')
no_isort_regex = [re.compile(br'^#.*no-isort', flags=re.M), re.compile(br'^ *sys\.path\.append', flags=re.M)]


def clean_file(p: Path, content: bytes):
    content, changes = trailing_white.subn('b\n', content)
    if changes:
        p.write_bytes(content)
        print(f'{p}: {changes} line{"s" if changes > 1 else ""} cleaned')


def main():
    auto_check = Path('./.auto-format')
    if not auto_check.exists():
        print(f'{auto_check} does not exist, not running')
        return

    try:
        conf = json.loads(auto_check.read_text())
    except ValueError:
        conf = {}

    file = sys.argv[1]
    file_path = Path(file)
    if not file_path.exists():
        raise RuntimeError(f'file path does not exist "{file_path}"')

    rel_path = file_path.relative_to(Path('.').resolve())
    exclude = conf.get('exclude')
    # print(exclude, rel_path)
    if exclude and str(rel_path) in exclude:
        print('file excluded from formatting')
        return

    print(f'running formatting on "{file_path}"...')
    content = file_path.read_bytes()
    clean_file(file_path, content)

    try:
        no_isort = next(r for r in no_isort_regex if r.search(content))
    except StopIteration:
        isort_main(['-rc', '-w', '120', file])
    else:
        print(f'"{no_isort}" found in file, not running isort')

    black_path = Path(__file__).parent / 'env/bin/black'
    subprocess.run([str(black_path), '-S', '-l', '120', '--target-version', 'py36', file], check=True)


if __name__ == '__main__':
    main()
