#!/usr/bin/env python3
"""Check published entry points, pinned source identities, and imported-law checking."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BEND = os.environ.get('BEND', str(Path.home() / '.bend/bin/bend'))
ENTRIES = ['PROOF.bend', 'package.bend']
PROBE = '\n\nlaw unused_false_audit_probe:\n  {0n == 1n : Nat}\n\ndef unused_false_audit_probe(): {==}\n'


def main():
    manifest = json.loads((ROOT / 'BENDHUB.json').read_text())
    identities = {}
    total = 0
    for name, expected in manifest['source_files'].items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT):
            raise RuntimeError(f'Manifest path escapes project: {name}')
        content = path.read_bytes()
        actual = hashlib.sha256(content).hexdigest()
        if actual != expected:
            raise RuntimeError(f'Published source hash mismatch: {name}')
        identities[name] = actual
        total += len(content)
    if total != manifest['bytes']:
        raise RuntimeError('Published source byte count mismatch')
    evidence = {'bend': subprocess.check_output([BEND, '--version'], text=True).strip(),
                'source_sha256': identities, 'source_bytes': total,
                'scope': 'Local source identity against the committed BendHub manifest; no network fetch or new publication.',
                'positive_checks': [], 'negative_checks': []}
    # Check both proof entries and the runtime-only wrapper before mutation.
    for entry in [*ENTRIES, 'keccak.bend']:
        result = subprocess.run([BEND, entry], cwd=ROOT, capture_output=True, text=True, timeout=120)
        if result.returncode != 0 or 'All terms check.' not in result.stdout:
            raise RuntimeError(f'Baseline entry failed: {entry}\n{result.stdout}\n{result.stderr}')
        evidence['positive_checks'].append({'entry': entry, 'exit': result.returncode,
                                           'stdout': result.stdout, 'stderr': result.stderr})
    # The false law has no call site. Its rejection tests import closure, not reachability.
    with tempfile.TemporaryDirectory(prefix='keccak-import-check-') as directory:
        root = Path(directory)
        for name in ['src', 'spec', 'proofs']:
            shutil.copytree(ROOT / name, root / name)
        for source in ROOT.glob('*.bend'):
            shutil.copy2(source, root / source.name)
        with (root / 'proofs/api.bend').open('a') as output:
            output.write(PROBE)
        for entry in ENTRIES:
            result = subprocess.run([BEND, entry], cwd=root, capture_output=True, text=True, timeout=120)
            diagnostic = result.stdout + result.stderr
            rejected = (result.returncode != 0 and 'unused_false_audit_probe' in diagnostic
                        and 'expected : 0n' in diagnostic and 'observed : 1n' in diagnostic)
            if not rejected:
                raise RuntimeError(f'Unused false law was not rejected as expected: {entry}\n{diagnostic}')
            evidence['negative_checks'].append({'entry': entry, 'exit': result.returncode,
                                                'unused_false_law_rejected': True, 'diagnostic': diagnostic})
    (ROOT / 'build').mkdir(exist_ok=True)
    (ROOT / 'build/proof-imports.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(f'Published source manifest: {len(identities)} files, {total} bytes verified')
    print('Published entries checked; both proof entries reject an unused imported false law')


if __name__ == '__main__':
    main()
