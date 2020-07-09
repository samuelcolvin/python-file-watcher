#!/home/samuel/code/file-watchers/env/bin/python
import json
import re
import subprocess
import sys
from pathlib import Path

trailing_white = re.compile(b' +\n')
no_isort_regex = [re.compile(br'^#.*no-isort', flags=re.M), re.compile(br'^ *sys\.path\.append', flags=re.M)]
root_dir = Path('.').resolve()


def echo(*args):
    print(*args, flush=True)


def clean_line_endings(p: Path, content: bytes):
    content, changes = trailing_white.subn(b'\n', content)
    if changes:
        p.write_bytes(content)
        echo(f'{p}: {changes} line{"s" if changes > 1 else ""} cleaned')


def main():
    conf = {}
    auto_check = Path('./.auto-format')
    if auto_check.exists():
        try:
            conf = json.loads(auto_check.read_text())
        except ValueError:
            pass

    file = sys.argv[1]
    file_path = Path(file)
    if not file_path.exists():
        raise RuntimeError(f'file path does not exist "{file_path}"')
    if '/site-packages/' in str(file_path):
        return

    rel_path = file_path.relative_to(Path('.').resolve())
    exclude = conf.get('exclude')
    str_path = str(rel_path)
    if exclude and any(re.fullmatch(ex, str_path) for ex in exclude):
        echo(f'file "{str_path}" excluded from formatting, exclude: {exclude}')
        return

    echo(f'running formatting on "{file_path}"...')
    content = file_path.read_bytes()
    echo('running clean_line_endings...')
    clean_line_endings(file_path, content)

    env_dir = conf.get('env_dir', 'env')
    try:
        no_isort = next(r for r in no_isort_regex if r.search(content))
    except StopIteration:
        isort_path = root_dir / env_dir / 'bin/isort'
        if isort_path.exists():
            echo('running isort...')
            subprocess.run([str(isort_path), '-rc', '-w', '120', file], check=True)
        else:
            print('isort not installed')
    else:
        echo(f'"{no_isort.pattern}" found in file, not running isort')

    black_path = root_dir / env_dir / 'bin/black'
    if black_path.exists():
        echo('running black...')
        subprocess.run([str(black_path), '-S', '-l', '120', '--target-version', 'py37', file], check=True)
    else:
        print('black not installed')


if __name__ == '__main__':
    main()
