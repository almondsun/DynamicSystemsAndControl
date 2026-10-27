"""Local Buck document organizer. Python standard library only; never moves sources."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1] / 'vendor_assets_local'
FIELDS = ['bom_reference', 'mpn', 'lcsc', 'original_name', 'source_path',
          'origin', 'destination', 'category', 'sha256', 'classification_status',
          'verification_status', 'redistribution_status', 'detail']
EXTENSIONS = {'.pdf', '.kicad_sym', '.lib', '.dcm', '.kicad_mod', '.mod',
              '.step', '.stp', '.wrl', '.zip', '.iges', '.igs', '.stl',
              '.obj', '.lbr', '.bxl', '.dra', '.pad', '.txt', '.md', '.html'}
PARTIAL = {'.part', '.partial', '.crdownload', '.download', '.tmp'}


def downloads() -> Path:
    """Resolve the current user's Windows shell setting, including redirection."""
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                       r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
        value, _ = winreg.QueryValueEx(key, '{374DE290-123F-4565-9164-39C4925E467B}')
    path = Path(os.path.expandvars(value)).resolve(strict=True)
    with os.scandir(path) as entries:
        next(entries, None)  # Exercise directory-read permission without reading unrelated files.
    return path


def digest(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def safe_folder(mpn: str) -> str:
    # Reversible exact MPN encoding for Windows-invalid characters; preserve case.
    from urllib.parse import quote
    encoded = quote(mpn, safe='-_.()')
    if encoded.endswith('.'):
        encoded = encoded[:-1] + '%2E'
    if encoded.split('.')[0].upper() in {'CON', 'PRN', 'AUX', 'NUL'} | {
            f'{kind}{n}' for kind in ('COM', 'LPT') for n in range(1, 10)}:
        encoded = '%'+format(ord(encoded[0]), '02X')+encoded[1:]
    return encoded


def load_config(root: Path) -> dict:
    config = json.loads((root / 'components.json').read_text(encoding='utf-8'))
    seen, folders = set(), set()
    for part in config['components']:
        mpn = part['mpn']
        if not isinstance(mpn, str) or not mpn or mpn != mpn.strip():
            raise ValueError('MPN must be a nonempty exact string without edge spaces')
        folder = safe_folder(mpn).casefold()
        if mpn in seen or folder in folders:
            raise ValueError('Duplicate MPN or Windows folder collision: '+mpn)
        seen.add(mpn)
        folders.add(folder)
        if part.get('lcsc') and not re.fullmatch(r'C[0-9]+', part['lcsc']):
            raise ValueError('Invalid configured LCSC code')
        aliases = part.get('aliases', [])
        if not isinstance(aliases, list) or any(not isinstance(a, str) or not a.strip() for a in aliases):
            raise ValueError('Aliases must be nonempty strings')
        for name, category in part.get('files', {}).items():
            if Path(name).name != name or category not in {'datasheet', 'symbol', 'footprint', '3d', 'auxiliary'}:
                raise ValueError('files must map exact basenames to supported categories')
    return config


def identify(name: str, config: dict) -> list[dict]:
    matches = []
    for part in config['components']:
        tokens = [part['mpn'], *part.get('aliases', [])]
        if part.get('lcsc'):
            tokens.append(part['lcsc'])
        # No fuzzy matching, case folding, content-based MPN guessing or prefix matching.
        stem = Path(name).stem
        if name in part.get('files', {}) or any(
                re.search(r'(?<![A-Za-z0-9.+\-])'+re.escape(token)+r'(?![A-Za-z0-9.+\-])', stem)
                for token in tokens):
            matches.append(part)
    return matches


def sexpr_valid(text: str, head: str) -> bool:
    if not text.lstrip().startswith('('+head):
        return False
    depth, quoted, escaped = 0, False, False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == '\\':
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char == '(':
            depth += 1
        elif char == ')':
            depth -= 1
            if depth < 0:
                return False
    return depth == 0 and not quoted


def inspect_file(path: Path) -> tuple[str, str]:
    """Basic signature/truncation checks; never electrical/mechanical verification."""
    size = path.stat().st_size
    if not size:
        return 'suspected_corrupt', 'empty file'
    ext = path.suffix.lower()
    if ext == '.zip':
        try:
            with zipfile.ZipFile(path) as archive:
                entries = archive.infolist()
                if sum(i.file_size for i in entries) > 100_000_000 or len(entries) > 2000:
                    return 'not_checked', 'archive exceeds CRC-check limits; no extraction'
                if archive.testzip():
                    return 'suspected_corrupt', 'ZIP CRC failure'
            return 'basic_check_passed', 'ZIP CRC checked; contents not extracted or trusted'
        except (OSError, ValueError, RuntimeError, zipfile.BadZipFile, NotImplementedError) as exc:
            return 'suspected_corrupt', 'ZIP unreadable: '+str(exc)
    with path.open('rb') as stream:
        prefix = stream.read(256)
        stream.seek(max(0, size-4096))
        tail = stream.read()
    if ext == '.pdf':
        ok = prefix.startswith(b'%PDF-') and b'%%EOF' in tail
    elif ext in {'.step', '.stp'}:
        ok = b'ISO-10303-21;' in prefix and b'END-ISO-10303-21;' in tail
    elif ext == '.wrl':
        ok = prefix.startswith(b'#VRML')
    elif ext in {'.kicad_sym', '.kicad_mod'}:
        if size > 20_000_000:
            return 'not_checked', 'KiCad file exceeds structural-check limit'
        try:
            value = path.read_text(encoding='utf-8-sig')
            ok = sexpr_valid(value, 'kicad_symbol_lib' if ext == '.kicad_sym' else 'footprint')
        except UnicodeError:
            ok = False
    else:
        return 'not_checked', 'format requires manual inspection'
    return ('basic_check_passed', 'signature/basic structure only') if ok else (
        'suspected_corrupt', 'invalid signature or incomplete structure')


def category_for(path: Path, part: dict) -> str:
    explicit = part.get('files', {}).get(path.name)
    if explicit:
        return explicit
    ext = path.suffix.lower()
    if ext == '.pdf':
        return 'datasheet' if re.search(r'(?i)(?:^|[_ -])datasheet(?:$|[_ -])', path.stem) else ''
    return {'.kicad_sym': 'symbol', '.kicad_mod': 'footprint',
            '.step': '3d', '.stp': '3d', '.wrl': '3d'}.get(ext, '')


def copy_verified(source: Path, directory: Path, sha: str) -> Path:
    for parent in [directory, *directory.parents]:
        if parent.is_symlink():
            raise ValueError('Destination ancestor symlink refused: '+str(parent))
    directory.mkdir(parents=True, exist_ok=True)
    # Content-addressed directory preserves original basename and prevents collisions.
    target = directory / sha / source.name
    target.parent.mkdir(exist_ok=True)
    for existing in target.parent.iterdir():
        if existing.is_symlink() or not existing.is_file() or digest(existing) != sha:
            raise ValueError('Unexpected or damaged content in hash directory: '+str(existing))
        if digest(source) != sha:
            raise ValueError('Source changed during deduplication')
        return existing
    if target.is_symlink():
        raise ValueError('Destination symlink refused')
    if target.exists():
        if digest(target) != sha:
            raise ValueError('Existing destination differs; refusing overwrite: '+str(target))
        return target
    try:
        with source.open('rb') as src, target.open('xb') as dst:
            shutil.copyfileobj(src, dst)
        if digest(target) != sha or digest(source) != sha:
            raise ValueError('Source changed or copy verification failed: '+str(source))
    except BaseException:
        # Leave incomplete copies for explicit review; never delete original downloads.
        raise
    return target


class Organizer:
    def __init__(self, root: Path, inbox: Path, settle: float):
        self.root, self.inbox, self.settle = root, inbox, settle
        self.observed = {}
        self.errors = []
        manifest = root / 'manifest.csv'
        with manifest.open(newline='', encoding='utf-8-sig') as stream:
            self.rows = list(csv.DictReader(stream))

    def scan(self):
        config = load_config(self.root)  # Reload for every batch; no model needed.
        config_hash = digest(self.root / 'components.json')
        known = {(r['source_path'], r['sha256'], r['detail'].split('config=')[-1]) for r in self.rows}
        count = 0
        for source in sorted(self.inbox.rglob('*')):
            if source.is_symlink() or not source.is_file() or not source.resolve().is_relative_to(self.inbox.resolve()):
                continue
            if any(p.suffix.lower() in PARTIAL for p in [source, *source.parents]):
                continue
            if source.suffix.lower() not in EXTENSIONS:
                continue
            try:
                stat = source.stat()
                stamp = (stat.st_size, stat.st_mtime_ns)
                previous = self.observed.get(source)
                now = time.monotonic()
                if previous is None or previous[0] != stamp:
                    self.observed[source] = (stamp, now)
                    continue
                if now-previous[1] < self.settle or time.time()-stat.st_mtime < self.settle:
                    continue
                sha = digest(source)
                if (source.stat().st_size, source.stat().st_mtime_ns) != stamp:
                    self.observed.pop(source, None)
                    continue
                key = (str(source), sha, config_hash)
                if key in known:
                    continue
                matches = identify(source.name, config)
                part = matches[0] if len(matches) == 1 else {}
                verification, detail = inspect_file(source)
                category = category_for(source, part) if part else ''
                status = 'classified' if part and category and verification == 'basic_check_passed' else 'pending_review'
                if len(matches) != 1:
                    detail += '; '+('ambiguous: '+', '.join(p['mpn'] for p in matches) if matches else 'no configured exact match')
                elif not category:
                    detail += '; category requires explicit filename mapping'
                if source.suffix.lower() == '.zip':
                    status = 'pending_review'
                    detail += '; archive requires manual inspection/unpacking into dedicated inbox'
                duplicate = next((r for r in self.rows if r['sha256'] == sha), None)
                if duplicate:
                    detail += '; duplicate content of '+duplicate['source_path']
                base = (self.root / 'component_library' / safe_folder(part['mpn']) / category
                        if status == 'classified' else self.root / 'pendiente_revision')
                if part:
                    for kind in ('datasheet', 'symbol', 'footprint', '3d'):
                        (self.root / 'component_library' / safe_folder(part['mpn']) / kind).mkdir(parents=True, exist_ok=True)
                target = copy_verified(source, base, sha)
                row = dict(zip(FIELDS, [part.get('bom_reference', ''), part.get('mpn', ''),
                    part.get('lcsc', ''), source.name, str(source), part.get('origin', ''),
                    str(target.relative_to(self.root)), category or 'unknown', sha, status,
                    verification, 'not_reviewed', detail+'; config='+config_hash]))
                self.rows.append(row)
                known.add(key)
                self.save()
                count += 1
                print(status+': '+source.name, flush=True)
            except (OSError, ValueError) as exc:
                message = str(source)+': '+str(exc)
                if message not in self.errors:
                    self.errors.append(message)
                print('RETRY / REVIEW: '+str(source)+': '+str(exc), file=sys.stderr, flush=True)
        self.report()
        return count

    def save(self):
        temporary = self.root / 'manifest.csv.tmp'
        with temporary.open('w', newline='', encoding='utf-8-sig') as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(self.rows)
        temporary.replace(self.root / 'manifest.csv')

    def report(self):
        pending = [r for r in self.rows if r['classification_status'] == 'pending_review']
        text = ['# Reporte local Buck', '', f'Registros históricos: {len(self.rows)}',
                f'Registros pendientes: {len(pending)}', '',
                'Las revisiones anteriores se conservan; consulte el último registro de cada origen.',
                'SHA-256 y controles básicos no acreditan compatibilidad ni redistribución.', '']
        text += [f"- {r['original_name']}: {r['detail'].split('; config=')[0]}" for r in pending]
        text += ['', 'Errores de copia/lectura pendientes (se reintentan):', *self.errors]
        (self.root / 'pending_report.md').write_text('\n'.join(text)+'\n', encoding='utf-8')


def initialize(root: Path):
    root.mkdir(parents=True, exist_ok=True)
    for name in ('component_library', 'pendiente_revision'):
        (root / name).mkdir(exist_ok=True)
    config = root / 'components.json'
    if not config.exists():
        config.write_text(json.dumps({'components': []}, indent=2)+'\n', encoding='utf-8')
    if not (root / 'manifest.csv').exists():
        with (root / 'manifest.csv').open('x', newline='', encoding='utf-8-sig') as stream:
            csv.DictWriter(stream, fieldnames=FIELDS).writeheader()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['init', 'once', 'watch'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--inbox', type=Path, help='Dedicated Buck directory only; never Downloads itself')
    parser.add_argument('--settle', type=float, default=10)
    parser.add_argument('--interval', type=float, default=3)
    args = parser.parse_args()
    if args.settle < 0 or args.interval <= 0:
        parser.error('settle must be >= 0 and interval > 0')
    download_path = downloads()
    inbox = (args.inbox or download_path / 'Buck_component_inbox').resolve()
    if inbox == download_path or download_path.is_relative_to(inbox):
        parser.error('Refusing Downloads or an ancestor as inbox')
    root = args.root.resolve()
    if inbox == root or inbox.is_relative_to(root) or root.is_relative_to(inbox):
        parser.error('Inbox and output must be separate trees')
    initialize(root)
    inbox.mkdir(parents=True, exist_ok=True)
    print('Downloads: '+str(download_path)+'\nInbox: '+str(inbox)+'\nLibrary: '+str(root), flush=True)
    lock = root / '.organizer.lock'
    with lock.open('x', encoding='ascii') as stream:
        stream.write(str(os.getpid()))
    try:
        organizer = Organizer(root, inbox, args.settle)
        if args.mode == 'init':
            load_config(root)
            organizer.report()
        elif args.mode == 'once':
            organizer.scan()
            time.sleep(args.settle)
            organizer.scan()
        else:
            print('Watching; Ctrl+C stops. Configuration reloads each scan.', flush=True)
            while True:
                organizer.scan()
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print('Stopped. Originals preserved.')
    finally:
        lock.unlink()


if __name__ == '__main__':
    main()
