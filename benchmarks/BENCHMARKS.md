# Four-way Keccak-256 benchmark

All participants hash Ethereum Keccak-256 (136-byte rate, 24 rounds, `0x01`
suffix), not SHA3-256. The primary results are `comparison-arm64.json`.

| Participant | Exact implementation |
|---|---|
| Bend | Stock Bend 2.0.16, packed U32 input/output, fixed scalar permutation state |
| Optimized C | XKCP `plain-64bits`, fully unrolled, upstream `KeccakP-1600-opt64.c` |
| Portable C (compact) | XKCP `compact`, upstream `KeccakP-1600-compact64.c` |
| Lean 4 → native C | KeccakEngine `Spec.keccakF1600` and unchanged upstream sponge, compiled with Lean 4.29.0 |

**Both C implementations are portable C.** “Optimized” distinguishes the fully
unrolled implementation from the compact implementation, not C from assembly or
hardware acceleration. Neither C participant uses a handwritten assembly backend
or explicit SHA-3 intrinsics. The ≤2× target remains against **optimized C**; the
compact reference does not replace it or relax the target.

Both C variants use the same sponge/benchmark wrapper and pinned XKCP revision
`eb5244d6b95fb1c434b211bac293093e18aa8fd1`. The upstream permutation sources are
unmodified. Bend and C use Apple Clang 17 with `-O3 -march=native -std=c11`.
Lean uses its pinned 4.29.0 toolchain, bundled Clang 19.1.2, and
`-O3 -march=native`. This is a native executable benchmark, not Lean interpretation.

## Workload and validation

Identical deterministic messages, from empty input to 1 MiB, are generated before
timing. Each participant receives one warmup and five measured batches, with
participant order rotated. Counts are calibrated independently toward 250 ms to
accommodate different speeds and Bend's millisecond timer resolution. A hash
longer than 250 ms uses one hash per batch. Reported time is median batch time
divided by its actual count. All individual samples and counts are retained.

Timing includes each hash and a retained checksum, but excludes input generation,
process startup, hexadecimal formatting, and correctness validation. Bend clones
its consumed packed input and allocates its digest; Lean reuses its immutable
ByteArray; C copies into preallocated scratch. These ownership/allocation costs
are intentionally disclosed and are not claimed to be identical.

All timed checksums are validated against PyCryptodome Keccak; C and Lean also
print a full digest outside the timer and that digest is checked on every run.
Full-digest checks independently cover every length 0–273, 4 KiB, and 64 KiB for
each reference. Bend additionally checks two invalid capacities. The compiled
Lean loop was inspected to confirm it calls the hash on every iteration.

Lean's benchmark binding selects the exact function chosen by upstream's
`implemented_by` attribute. Its permutation and sponge files are copied unchanged;
the separate upstream proof chain is not rebuilt. See [LEAN.md](LEAN.md) for the
binding, source identity, and generated-code findings. This benchmark does not
claim that KeccakEngine is the fastest possible Lean implementation.

The host is a shared Apple M4 machine. Timing variation is visible in the raw
samples; these are local measurements, not cross-platform or isolated-host
performance guarantees. Older JSON files are historical runs and should not be
mixed into the current comparison.

## Reproduce

Install stock Bend, Clang, Git, uv, and elan/lake, then run from the repository root:

```sh
uv sync
uv run python tools/build.py
uv run python tools/validate.py
uv run python tools/build_lean.py --lake lake
uv run python tools/benchmark_all.py
```

The build fetches pinned references into ignored `vendor/` directories. The Lean
build uses upstream's pinned toolchain. Source and binary SHA-256 identities,
compiler versions, C implementations, input sizes, batch counts, and samples are
recorded in `comparison-arm64.json`.
