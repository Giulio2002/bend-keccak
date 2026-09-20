# Stock Bend optimization investigation

The target is `Bend time / optimized portable C time <= 2` across the benchmark
workloads. **The target has not been reached.** The production implementation and
its full public sponge proof are retained; experimental candidates are not
silently substituted for the verified library.

The investigation inspected stock Bend 2.0.16 compiler source and generated C/ARM
assembly. Stock native word types include U32, F32, and bounded Nat, not a native
U64 bitwise lane. The production Keccak state therefore uses fifty U32 components.
Generated rotations already lower to ARM `extr` instructions. Compared with the
25-lane native-U64 C reference, paired arithmetic and register spills remain major
structural differences. This is not a proof that a 2x target is impossible.

Experiments included even/odd bit-interleaved lanes, pre-interleaved constants,
1/2/4/6/12/24-round loops, a fixed 24-round specialization with literal constants,
aggressive SLP vectorization, CPU tuning flags, paired constant lookup, and
independent row schedules for the two fused rounds. The bit-interleaved prototype
reached about 3.1–3.4x C in probes but does not yet have its representation bridge
proof. It is not the published production path. Larger unrolling and aggressive
SLP were often slower. Minor scheduling differences were not sufficiently stable
on the shared host to claim a new speedup.

An attempted monolithic proof for fixed 24-round expansion was stopped without a
successful proof result; this is not counted as a logical rejection. Likewise,
experiments without complete proofs are not advertised as verified optimizations.
No foreign implementation, patched generated C, compiler fork, or weaker C
baseline was adopted to manufacture a target pass.

Probe data is retained in `benchmarks/experiments/`. These are exploratory timings
on a changing shared-host load; they are not the release benchmark. Some probes
ran while build/proof work was active and are unsuitable for close comparisons.
Use `comparison-arm64.json` for the current four-way comparison; the other JSON files are historical runs. The next accepted optimization
must improve paired measurements and retain the existing public laws.
