#!/usr/bin/env python3
"""Frozen gates for proof-swarmer: actual proof suite and unchanged public hash costs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
from Crypto.Hash import keccak

ROOT = Path(__file__).resolve().parents[1]
BEND = os.environ.get('BEND', str(Path.home() / '.bend/bin/bend'))
SIZES = [0, 32, 64, 135, 136, 137, 1024, 16384, 65536, 1048576]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('gate', choices=['check', 'benchmark'])
    args = parser.parse_args()
    os.chdir(ROOT)
    (ROOT / 'build').mkdir(exist_ok=True)
    if args.gate == 'check':
        subprocess.run([sys.executable, 'tools/validate.py', '--mutations'], check=True)
        subprocess.run([sys.executable, 'tools/check_proof_imports.py'], check=True)
        print('SWARM PROOFS DIFFERENTIAL TESTS AND MUTATIONS PASSED')
        return
    subprocess.run([BEND, 'benchmarks/driver.bend', '-o', 'build/swarm-bench.c'], check=True)
    subprocess.run(['clang', '-O3', '-march=native', '-std=c11', 'build/swarm-bench.c',
                    '-lpthread', '-lm', '-o', 'build/swarm-bench'], check=True)
    rows = []
    metrics = {}
    for size in SIZES:
        depth = max(0, (((size + 3) // 4) - 1).bit_length())
        capacity = (1 << depth) * 4
        count = max(64, min(524288, 64 * 1024 * 1024 // max(1, size)))
        data = b''.join(((i * 2654435761 + 42) & 0xffffffff).to_bytes(4, 'little')
                        for i in range(capacity // 4))[:size]
        expected = (int.from_bytes(keccak.new(digest_bits=256, data=data).digest()[:4], 'little') * count) & 0xffffffff
        env = {**os.environ, 'KECCAK_SIZE': str(size), 'KECCAK_DEPTH': str(depth), 'KECCAK_COUNT': str(count)}
        samples = []
        for repetition in range(6):
            result = subprocess.run(['build/swarm-bench', '--threads', '1', '--gpu', 'off'],
                                    env=env, capture_output=True, text=True, check=True, timeout=120)
            lines = result.stdout.splitlines()
            if len(lines) != 2 or int(lines[1]) != expected:
                raise RuntimeError(f'Benchmark checksum mismatch for {size} bytes')
            if repetition:
                samples.append(float(lines[0].split('=')[1]) * 1000 / count)
        metrics[f'keccak256_{size}_bytes_us'] = statistics.median(samples)
        rows.append({'bytes': size, 'count': count, 'samples_us': samples, 'checksum_verified': True})
        print(size, metrics[f'keccak256_{size}_bytes_us'], flush=True)
    evidence = {'warmups': 1, 'samples': 5, 'rows': rows,
                'compiler': subprocess.check_output(['clang', '--version'], text=True).splitlines()[0],
                'bend': subprocess.check_output([BEND, '--version'], text=True).strip(),
                'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in sorted((ROOT / 'src').glob('*.bend'))},
                'binary_sha256': hashlib.sha256((ROOT / 'build/swarm-bench').read_bytes()).hexdigest(),
                'boundary': 'Same public Bend driver and batch counts as tools/benchmark.py; one warmup and five samples. Input clone and digest allocation included. No C reference changed.'}
    (ROOT / 'build/swarm-benchmark-evidence.json').write_text(json.dumps(evidence, indent=2) + '\n')
    (ROOT / 'build/swarm-metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')


if __name__ == '__main__':
    main()
