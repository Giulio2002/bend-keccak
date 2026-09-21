# Reviewed proof-swarmer experiment — 2026-09-21

This was a live `claude -p` / DeepSeek V4.1 Flash experiment against commit
`b36ae58`, with an additional frozen `tools/swarm_gate.py` adapter. It is an
adversarial review experiment, **not a formal completeness certificate**.

The run stopped as `incomplete_audit` before any worker was launched. All nine
specialist reports eventually passed mechanical validation, but the orchestrator
reported unresolved audit gaps and produced a repair brief that was not reliable
enough to apply. No automatic runtime or proof repair was accepted. This PR adds
reproducible checks and clarifies the existing proof boundary; it does not claim
to have repaired every alleged gap.

## What was independently established

| Area | Result | Evidence / remaining work |
|---|---|---|
| Existing public sponge proof | Passed | The frozen `PROOF.bend` gate passed. Existing law statements, proof definitions, production Bend code and independent spec files remain byte-for-byte unchanged. |
| Differential correctness | Passed | 278 cases on the interpreter and 278 on native C, using full formatted digests against PyCryptodome Keccak. |
| Existing mutation suite | Passed | All ten production mutations were rejected by the checker; timeouts were not accepted as rejections. |
| Imported but unused proofs | Checked directly | A temporary, unused `0n == 1n` law is rejected at its definition through both `PROOF.bend` and `package.bend`. The new checker reproduces this test. |
| Published source manifest | Checked locally | The 15 files and 149,853 bytes in `BENDHUB.json` match their recorded SHA-256 values. No new package was published or remote download verified by this check. |
| Hex formatting theorem | **Open proof obligation** | The formatter is exercised by differential tests but has no universal formatting-refinement theorem. README and CORRECTNESS now make this explicit. |
| Array tail reads | Memory-safety allegation rejected | Installed Base `Array.get.at` masks the index; emitted C `blk_at` does likewise. Padding discards unused values. This relies on the explicitly trusted Base/compiler semantics. |
| `%` equality rewrites | Bypass allegation rejected | The installed Bend guide documents `%e : P` as a checked equality rewrite. Base itself uses it. An unfamiliar construct is not an admission. |
| Performance | Baseline measured; no runtime patch | All ten original public-driver workloads were measured. No candidate was accepted, so these are baseline costs, not before/after speedups or an optimization claim. |

The hash-refinement theorem relates the actual packed-word API to the separate
packed-word sponge specification. That specification shares normative constants
and state representation with the implementation. The existing documentation
already excludes a separate bitstring-model equivalence theorem, cryptographic
security, constant-time execution, and compiler correctness. Stronger independent
models and additional mutation probes are useful follow-up work; they are not
established merely by this audit or by the existing checker pass.

## Why the automatic repair brief was rejected

The initial reports included overlapping allegations and false assumptions about
Bend. The correction pass fixed paths/citations and withdrew several allegations.
The orchestrator then adjudicated 80 original entries and added four more. Its
structured output labels 68 original entries `confirmed` and 12 `dismissed`;
these are **model classifications, not 68 independently verified defects**.

Specific problems in the final brief included:

- Confirming a retraction as though it were still an actionable defect, sometimes
  changing it into a different residual allegation under the same ID.
- Treating an explicitly trusted compiler/kernel boundary as a blocking audit
  gap, despite the configured scope excluding compiler correctness.
- Confusing an absent named convenience lemma with an absence of behavior from
  the existing universal refinement.
- Treating definitional equality as evidence that a theorem adds no constraint.
  The existing selected-round-count mutation is rejected; the theorem still
  constrains the concrete chosen round count.
- Retaining allegation titles that incorrectly say entry files are absent from
  the pinned source hashes: `BENDHUB.json` contains both. The narrower lack of a
  committed entry-check command was a legitimate harness improvement, now added.
- Interpreting timing variation as a provenance defect without consistently
  accounting for the shared-host variation already disclosed in README.

These issues prevented a trustworthy complete repair scope. The runner correctly
stopped at the unresolved-audit gate, before a worker could apply the brief.
Repair was blocked by audit quality and scope resolution, **not by a measured
candidate performance regression**. There was no candidate benchmark and no
claim that a formatter proof is impossible.

## Reproduce the checked evidence

```sh
uv sync
uv run python tools/swarm_gate.py check
uv run python tools/swarm_gate.py benchmark
```

The check command runs the original proof/differential/mutation suite, verifies
the published source manifest and entry files, and checks rejection of an unused
false imported law in temporary copies. The benchmark uses the same ten sizes,
public Bend driver, batch counts, checksum, compiler flags, one warmup and five
samples as the original Bend column. It emits fresh `build/swarm-metrics.json`
and `build/swarm-benchmark-evidence.json`; it does not change a C reference.
The swarmer host compares every row against its frozen baseline with a maximum
ratio of 1.0. The emitter itself is not the non-regression adjudicator.

[Generated-C identity](generated-c-identity.json) additionally confirms that the
stock compiler emitted exactly the same C before and after these additions.

The full pre-adjudication records and raw agent streams remain in the local run
store. [Model observations](model-observations.json) preserve the final machine
allegations, evidence, decisions and scope gaps for inspection, with workstation
paths sanitized. They are explicitly not an endorsed vulnerability or defect
list. [Baseline metrics](baseline-metrics.json), [original validation results](validation.json)
and [entry/import checks](proof-imports.json) are included alongside this review.

Future proof work should start with an independently specified formatting theorem
and a carefully reviewed domain, preserving all existing laws and runtime costs.
The audit's broader claims need individual source-backed adjudication before they
become implementation requirements. Merely documenting an unproved property does
not prove it or close that proof obligation.
