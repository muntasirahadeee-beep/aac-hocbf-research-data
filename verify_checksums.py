#!/usr/bin/env python3
"""Verify byte-exact SHA-256 hashes of all 141 copied original data files."""
import csv, hashlib, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'metadata' / 'SOURCE_FILES_SHA256.csv'

def main():
    bad = []
    with MANIFEST.open(newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        path = ROOT / r['package_path']
        if not path.is_file(): bad.append(f"MISSING {r['package_path']}"); continue
        b = path.read_bytes()
        if len(b) != int(r['file_size']): bad.append(f"SIZE {r['package_path']}"); continue
        digest = hashlib.sha256(b).hexdigest()
        if digest.lower() != r['sha256'].lower(): bad.append(f"HASH {r['package_path']}")
    actual = {str(p.relative_to(ROOT)) for p in (ROOT/'data').rglob('*') if p.is_file()}
    recorded = {r['package_path'] for r in rows}
    for p in sorted(actual - recorded): bad.append(f"UNMANIFESTED {p}")
    if bad:
        print('\n'.join(bad)); print(f"FAIL: {len(bad)} integrity issues"); return 1
    print(f"PASS: {len(rows)} original data files match source sizes and SHA-256 hashes")
    return 0
if __name__ == '__main__': sys.exit(main())
