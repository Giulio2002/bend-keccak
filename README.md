# bend-keccak

Ethereum **Keccak-256** in Bend 2.0.16, with native packed arrays, checked component laws, differential tests, and a benchmark against XKCP's optimized portable C. This is **not SHA3-256**: it uses the Keccak domain suffix `0x01`, a 136-byte rate, 512-bit capacity, and 24 Keccak-f[1600] rounds.

Current status: the **full public packed-input sponge refinement is kernel-checked**, including absorption, padding, repeated blocks, capacity rejection and all digest words. The generated C's round scheduling has been optimized to reduce register spills. It remains slower than optimized 64-bit C; see the measured results below.

## Install from BendHub

Published package: [0x48cee57f42dae6ba4c727fbf982cdd4d](https://hub.bend-lang.com/0x48cee57f42dae6ba4c727fbf982cdd4d).
With Bend installed, save this as `main.bend` in your project:

```bend
import Base
import 0x48cee57f42dae6ba4c727fbf982cdd4d/keccak.bend as Keccak

def show(result: Maybe<&1,Array<U32>>) -> String:
  match result:
    case None{}: "invalid length"
    case Some{digest}: Keccak.hex(digest)

def main() -> IO(Unit):
  # Little-endian word 0x00636261 contains "abc"; hash only its first three bytes.
  IO.print(show(Keccak.keccak256(Array.new(U32,0n,6513249),3n)))
```

Run `bend main.bend`. Bend downloads the content-addressed package automatically;
no repository clone is needed. Expected output:

```text
4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45
```

The runtime-only entry exports `Keccak.keccak256` and `Keccak.hex` and keeps proof
models out of the execution path. To import the entry that also checks and bundles
the public sponge proofs, replace the second import with:

```bend
import 0x48cee57f42dae6ba4c727fbf982cdd4d/package.bend as Keccak
```

The MIT-licensed bundle contains 15 Bend source files (149,853 bytes), including
independent specifications and proofs. It uses stock Bend, packed arrays, and no
cryptographic FFI. The exact proven boundary and trusted components are documented
in [CORRECTNESS.md](CORRECTNESS.md). The package hash pins immutable source.

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

## Benchmarks: Bend, optimized C, portable C, and Lean

Apple M4, sequential native hashing. **Microseconds per hash, median of five
measured batches after warmup; lower is faster.** All four participants ran in the
same comparison, with rotating order and independently calibrated batch counts.

| Input | Bend | Optimized C | Portable C (compact) | Lean 4 → C | Bend / optimized C |
|---|---:|---:|---:|---:|---:|
| empty | 0.645 | 0.180 | 0.344 | 644.783 | 3.59× |
| 32 B | 0.721 | 0.230 | 0.399 | 682.568 | 3.13× |
| 64 B | 0.725 | 0.185 | 0.364 | 675.621 | 3.92× |
| 135 B | 0.911 | 0.250 | 0.470 | 917.533 | 3.64× |
| 136 B | 1.688 | 0.463 | 0.906 | 1,670.994 | 3.65× |
| 137 B | 1.702 | 0.461 | 0.900 | 1,739.926 | 3.69× |
| 1 KiB | 6.781 | 1.919 | 3.486 | 7,041.913 | 3.53× |
| 16 KiB | 99.363 | 27.920 | 54.887 | 109,948.979 | 3.56× |
| 64 KiB | 370.690 | 112.747 | 206.978 | 424,324.542 | 3.29× |
| 1 MiB | 6,000.000 | 1,730.961 | 3,552.987 | 7,128,463.333 | 3.47× |

- **Optimized C:** XKCP `plain-64bits`, fully unrolled.
- **Portable C (compact):** XKCP `compact64`. Both C implementations are portable
  C, compiled at `-O3`; neither uses an assembly or explicit SHA-3 intrinsics backend.
- **Lean 4 → C:** KeccakEngine `053b9dd`, compiled through Lean 4.29.0's C backend
  into a native executable. This is not interpreted Lean and is not the unrelated
  C library leancrypto. Its generated code retains generic `BitVec`/array operations;
  the result is not a limit on what an optimized Lean implementation could achieve.

Bend and C use Apple Clang 17; Lean uses bundled Clang 19.1.2, all with
`-O3 -march=native`. Timings exclude input generation, startup, formatting, and
validation. Bend's consumed-input clone/digest allocation are included; C copies
into preallocated scratch and Lean reuses an immutable ByteArray. These differing
ownership/allocation costs are disclosed rather than treated as identical.

All timed checksums are checked against PyCryptodome Keccak; C and Lean full
digests are checked outside each timed batch. Separate full-digest validation
covers 276 cases per reference and 278 Bend cases, including capacity rejection.
The separate upstream Lean proof chain is not rebuilt; a benchmark binding selects
its exact `implemented_by` runtime function with unchanged permutation/sponge files.

**The ≤2× target against optimized C is not met.** The compact C column does not
replace that target. Shared-host load causes substantial sample variation; raw
samples and counts are retained. Older JSON files are historical runs.

For example, the 1 MiB per-hash sample ranges were Bend 5.98–8.05 ms, optimized C 1.64–3.84 ms, Lean 6,305.23–9,749.40 ms. These ranges show the load variation behind the medians.

[Raw results and source/binary identities](benchmarks/comparison-arm64.json) ·
[Methodology and reproduction](benchmarks/BENCHMARKS.md) ·
[Lean implementation details](benchmarks/LEAN.md) ·
[Optimization investigation](benchmarks/OPTIMIZATION.md).

```sh
uv run python tools/build.py
uv run python tools/validate.py
uv run python tools/build_lean.py --lake lake
uv run python tools/benchmark_all.py
```

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

## License

MIT; see [LICENSE](LICENSE). Fetched external benchmark references retain their own licenses.
