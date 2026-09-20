# Lean Keccak-256 comparison

This benchmark compares the existing verified Bend implementation against the
compiled runtime path of [KeccakEngine](https://github.com/AlexeyMilovanov/lean-keccak-unrolled)
at `053b9ddee2084332e0a7b25800bca9d4f56ffa8d`, plus XKCP's portable optimized C.
Lean is compiled through **Lean 4’s C backend into a native executable**, not run through `lean --run` or an interpreter. It is a comparison of these implementations, not an upper bound on Lean performance.

## What the Lean participant runs

Upstream `Core.lean` marks `keccakF1600_core` with
`@[implemented_by Spec.keccakF1600]`. Consequently its compiled permutation is
`Spec.keccakF1600`, not the proof-oriented unrolled circuit.

The benchmark copies upstream `Spec.lean` and `Sponge.lean` byte-for-byte into an
isolated build directory. A small benchmark-only `Core.lean` binds the core name
to that exact runtime function. This avoids rebuilding the separate, expensive
proof chain; **this run does not validate that upstream proof chain**. No theorem
is removed from the upstream checkout, and no proof is claimed for the shim.
The algorithm, constants, round loop, padding, and sponge code are unchanged.
There is no external C cryptographic implementation behind this Lean participant.

The toolchain is upstream's pinned Lean 4.29.0, with its bundled Clang 19.1.2 and
`-O3 -march=native`. Bend 2.0.16 and XKCP use Apple Clang 17 with
`-O3 -march=native -std=c11`. Compiler identities and the actual Lean compile
command are recorded alongside results.

## Timing and correctness

Inputs are identical deterministic byte strings, with sizes from zero to 1 MiB.
Both use Ethereum Keccak-256: 136-byte rate, 24 rounds, `0x01` domain suffix.
Input generation, process startup, full-digest validation, and hexadecimal output
are outside the timer. Hashing, output allocation, and a retained digest checksum
are inside it. The compiled Lean loop was inspected to confirm a hash call occurs
on every iteration.

Bend's consuming API clones its prepared packed array for each hash. Lean reuses
an immutable ByteArray without an explicit clone. XKCP copies into preallocated
scratch. These API ownership/allocation differences are included and disclosed;
the benchmark does not pretend they are identical memory-management workloads.

Each implementation receives one warmup and five measured batches, with run order
rotated. Batch counts are calibrated separately toward 250 ms because Bend's timer
has millisecond resolution and the implementations differ greatly in speed. The
median is divided by each participant's actual hash count. For workloads exceeding
250 ms per hash, a batch contains one hash. Raw counts and samples are retained.

All timed checksums are checked against PyCryptodome Keccak. Full digest tests also
cover every size 0–273 plus 4 KiB and 64 KiB: 276 matching Lean digests and 278 Bend
cases including two capacity rejections. Neither finite tests nor timing results
are presented as formal proofs.

## Why this Lean implementation is slow

The emitted C retains generic `BitVec.rotateLeft`, natural-number bit operations,
and generic array accesses/updates. Its `Array (BitVec 64)` state does not become
the fixed native scalar round code used by Bend or XKCP. This is a concrete
implementation/code-generation finding, not evidence that all Lean Keccak code
must have this performance. No attempt was made to optimize the Lean reference.

## Reproduce

With Bend, Clang, uv, Git, and elan/lake available:

```sh
uv sync
uv run python tools/build.py
uv run python tools/validate.py
uv run python tools/build_lean.py --lake lake
uv run python tools/benchmark_lean.py
```

`build_lean.py` uses the library's pinned `lean-toolchain`; elan may download it.
That historical three-way runner writes `benchmarks/lean-comparison-arm64.json`. The current release comparison uses `tools/benchmark_all.py` and writes `benchmarks/comparison-arm64.json`; see [BENCHMARKS.md](BENCHMARKS.md).
Measurements are from a shared machine, not an isolated performance lab.
