# bend-keccak

Ethereum **Keccak-256** in Bend 2.0.16, with native packed arrays, checked component laws, differential tests, and a benchmark against XKCP's optimized portable C. This is **not SHA3-256**: it uses the Keccak domain suffix `0x01`, a 136-byte rate, 512-bit capacity, and 24 Keccak-f[1600] rounds.

Current status: the **full public packed-input sponge refinement is kernel-checked**, including absorption, padding, repeated blocks, capacity rejection and all digest words. The generated C's round scheduling has been optimized to reduce register spills. It remains slower than optimized 64-bit C; see the measured results below.

## API

```bend
import Base
import ./src/keccak.bend as K

# Three bytes: 61 62 63 ("abc"). Input is consumed.
def example() -> Maybe<&1,Array<U32>>:
  K.keccak256(Array.new(U32,0n,6513249),3n)
```

`keccak256(words: Array<U32>, byte_length: Nat) -> Maybe<&1,Array<U32>>`

- Input words contain four **little-endian** bytes each. Word zero contains the first four bytes.
- A successful result contains exactly eight little-endian U32 words: 32 digest bytes. Use `src/hex.bend` for conventional byte-order hexadecimal display.
- Logical byte length must not exceed four times the array's reported capacity; otherwise returns `None`.
- Unused bytes in the last input word and unused trailing array slots are ignored. An empty message uses any valid allocated array and length zero.
- Use balanced arrays created by `Array.new` / `Array.set`; follow Base.Array's representation contract.
- Hash input/output and temporary storage use native arrays; state is a fixed record of 25 two-U32 lanes. There are **no runtime linked lists, array/list conversions, foreign calls, or modified compiler requirements**.

The installed Bend has U32 but no native U64. Each lane therefore uses low/high halves. Fixed rotations, two-round fusion, and packed padding avoid generic rotation calls and byte-wise padding loops. No list compatibility API is provided.

## Build and validate

Requires Bend 2.0.16, Clang, Python 3.11+, `uv`, and Git. `BEND` can override the default `$HOME/.bend/bin/bend` executable.

```sh
git clone https://github.com/Giulio2002/bend-keccak.git
cd bend-keccak
uv sync
uv run python tools/build.py
uv run python tools/validate.py --mutations
./build/main --threads 1 --gpu off
uv run python tools/benchmark.py
```

`tools/build.py` fetches the pinned XKCP reference **for comparison only**. The Bend library has no runtime dependency on it. Both native benchmarks compile with `clang -O3 -march=native -std=c11`.

Validation checks all root laws through `PROOF.bend`, 278 differential cases on each backend, and ten mutations, all rejected by the proof checker. Differential cases cover every message length 0–273, 4 KiB and 64 KiB messages, dirty unused storage, and invalid capacities. Reference: PyCryptodome's **Keccak** API, not hashlib.sha3_256. Empty and `abc` known-answer examples are in `main.bend`.

## Bend versus Lean Keccak-256

Apple M4, sequential native hashing, medians of five batches. **Microseconds per hash; lower is better.**

| Input | Bend | Lean KeccakEngine | XKCP C | Lean / Bend |
|---|---:|---:|---:|---:|
| empty | 0.496 | 482.568 | 0.135 | 973× |
| 32 B | 0.500 | 494.125 | 0.136 | 988× |
| 64 B | 0.512 | 499.357 | 0.139 | 976× |
| 136 B | 0.996 | 1,023.011 | 0.284 | 1,027× |
| 1 KiB | 3.953 | 4,067.723 | 1.158 | 1,029× |
| 16 KiB | 58.250 | 60,480.062 | 16.309 | 1,038× |
| 64 KiB | 231.490 | 241,809.042 | 65.283 | 1,045× |
| 1 MiB | 3,887.097 | 4,293,987.417 | 1,148.693 | 1,105× |

This measures [KeccakEngine](https://github.com/AlexeyMilovanov/lean-keccak-unrolled)
at `053b9dd` with Lean 4.29.0. Its compiled path uses generic `BitVec 64` and array
operations; this result is **not a claim about the fastest possible Lean implementation**.
A benchmark-only binding selects the same runtime function as upstream's
`implemented_by` attribute. The upstream permutation and sponge source files are
unchanged; its separate proof chain was not rebuilt. See the
[methodology and reproduction commands](benchmarks/LEAN.md).

Both implementations passed matching full-digest tests (276 Lean, 278 Bend cases
including capacity rejection). Every timed checksum was validated. Input preparation
is excluded; Bend's required input clone is included, while Lean reuses an immutable
ByteArray. Clang `-O3 -march=native` is used; Lean uses its bundled Clang 19 and
Bend/XKCP use Apple Clang 17. This is a shared-host measurement.

[Raw samples and source/binary identities](benchmarks/lean-comparison-arm64.json).
The **at-most-2×-C target is not met**: the measured production implementation is
roughly 3.4–3.7× C. [Optimization investigation](benchmarks/OPTIMIZATION.md).
Unproved experimental variants have not replaced the public implementation.

## Earlier C-only measurements

Apple M4, medians of five alternating samples after one warmup. Microseconds per hash:

| Input | Bend | XKCP portable 64-bit C | Bend / C |
|---|---:|---:|---:|
| 32 B | 0.650 | 0.176 | 3.69× |
| 64 B | 0.648 | 0.176 | 3.68× |
| 136 B | 1.279 | 0.351 | 3.65× |
| 1 KiB | 4.044 | 1.135 | 3.56× |
| 16 KiB | 62.256 | 17.510 | 3.56× |
| 64 KiB | 250.000 | 69.899 | 3.58× |
| 1 MiB | 3984.375 | 1134.219 | 3.51× |

All sizes, individual samples, environment, and checksum checks are in `benchmarks/results-arm64.json`. This is a local shared-host measurement, not a cross-platform guarantee. No Intel/AMD measurement has been performed for this library.

Input generation is excluded. Each iteration includes a packed input clone in Bend and an equivalent-size memcpy in C. Bend allocates its clone/result; C reuses preallocated scratch. Thus these are API-plus-copy measurements, not isolated permutation timings. Both retain a checked digest checksum. Full digest correctness is checked independently by the differential tests. Bend's timer has millisecond resolution; batched execution avoids sub-millisecond single-call measurements.

The C comparator is XKCP `plain-64bits`, default full unrolling, compiled directly from unmodified upstream source. It is a serious optimized portable reference, not a deliberately slow reference loop. No handwritten assembly or hardware-specific XKCP backend is selected. The generated ARM assembly for the inspected C build uses scalar 64-bit operations; the Bend version uses paired 32-bit operations and more register spills. This is an observed structural difference, not an exact decomposition of the runtime gap.

Generated-code inspection found 172 static spill instructions and 211 reload instructions in the original two-round function. Computing rho/pi and chi together by output row reduced those counts to 135 and 191, and shortened the function from 1,071 to 1,017 assembly lines. These are static assembly counts, not counts of dynamically executed loads per hash.

Paired repeated measurements show **1.13–1.16× speedup** for the retained row schedule against the prior schedule (`benchmarks/scheduling-experiment.json`). Six equivalent row orders were explored; their small differences were noisy, so the natural row order was retained. Earlier fixed-rotation and loop-fusion improvements are retained as well. Full 24-round unrolling had not improved the probe timings.

Absolute timings vary with other work on this shared machine. Use the paired schedule comparison for the attributable optimization effect; do not infer regressions or gains by comparing absolute times from different runs.

## Proof scope and project layout

See [CORRECTNESS.md](CORRECTNESS.md) for exact properties, limitations and trusted components.

- `src/`: production lane operations, fixed state, permutation, sponge and formatting.
- `spec/`: separate coordinate-based permutation specification, importing only Base and the shared state datatype.
- `proofs/`: full sponge refinement, permutation laws, affine-array proof model and component proofs.
- `LAWS.bend`, `PROOF.bend`: public law declarations and the proof gate.
- `tests/`: packed-array differential drivers.
- `benchmarks/`: independent C wrapper, Bend driver, raw measurements.
- `tools/`: reproducible validation, build, source pinning, benchmark and spec generation.
- `vendor/XKCP/`: fetched, ignored, pinned reference checkout.
- `build/`: ignored generated C/assembly/binaries, logs and exploratory artifacts.

## References

- XKCP: https://github.com/XKCP/XKCP/tree/eb5244d6b95fb1c434b211bac293093e18aa8fd1
- Optimized C: `lib/low/KeccakP-1600/plain-64bits/KeccakP-1600-opt64.c` and common macros.
- Algorithm reference: https://keccak.team/keccak_specs_summary.html

The algorithm and optimization strategy are inspired by the Keccak team's implementations. The Bend implementation uses its own source and paired U32 representation. Upstream XKCP files retain their original license notices in the reference checkout.
