# Correctness claims and boundaries

## Full public packed-input sponge refinement

`bend PROOF.bend` now checks `Laws.ethereum_keccak256`:

```bend
law ethereum_keccak256:
  for a: Array<U32>
  for +length: Nat
  {K.keccak256(a,length) == Sponge.keccak256_rounds(24n,a,length)
    : Maybe<&1,Array<U32>>}
```

This is a universal equality of the **actual public API**, including capacity rejection and the returned packed digest, to the separate packed-word Keccak sponge specification. It is not conditional on tests passing, finite input lengths, or a supplied permutation-correctness assumption.

The proof connects:

1. Every unrolled input read to an independently recursive gather operation.
2. XOR injection of exactly 34 little-endian U32 words into the first 17 lanes.
3. Every padding word to the specification's padding traversal, including the final `0x80` bit and the combined `0x81` last-byte case.
4. The optimized two-round loop to the coordinate-based theta → rho/pi → chi → iota specification, for arbitrary states, round counts and starting indices.
5. The round constants to the independently LFSR-generated specification table.
6. An arbitrary number of full 136-byte blocks followed by the padded last block.
7. Input-length decomposition, zero initial state, capacity checking, and digest extraction.
8. The public API's exact choice of 24 rounds, and equality of all eight returned words to the specification's output array.

`packed_sponge_correct` proves the generalized statement for every round count. `ethereum_keccak256` instantiates it at 24 for the public API. This lets the checker reuse a compositional proof instead of symbolically expanding 24 complete rounds at every absorption step.

## Specification and representation

`spec/permutation.bend` imports only Base and the neutral state/lane datatypes. Coordinates determine theta/rho/pi/chi; rho offsets and round constants are generated from coordinate and LFSR recurrences in `tools/generate_spec.py`. It does not call production lane or permutation functions.

`spec/sponge.bend` imports that independent permutation and the neutral types. Its recursive gather, padding traversal, lane injection, and tree-form digest definition are separate from the production unrolled reads and array-set digest construction. It never imports the production hash.

The public data model is packed little-endian U32 words with a logical byte length. The specification uses a list accumulator to describe collected words, and the proof reifies affine arrays into a duplicable mathematical tree. **These are specification/proof objects only. Neither is imported or executed by the hash implementation.** Runtime input/output remain native packed arrays, and the permutation state remains a fixed record.

As with any functional-correctness proof, the intended meaning of the specification must be reviewed. This development models 64-bit lanes as pairs of U32 values. It does not separately prove equivalence to a second, abstract bitstring implementation or to the XKCP C source. The proven boundary is the actual packed-array API versus the independently defined packed-word sponge specification.

No collision resistance, preimage resistance, constant-time execution, compiler correctness, or hardware correctness theorem is claimed.

## Component laws

The earlier component laws remain checked: universal round and constant refinement, fused-round expansion, digest size and each output word's order, capacity rejection, and padding-word rules. The new sponge proof composes these semantics through the real public implementation rather than leaving the absorption/padding path as a testing-only obligation.

## Empirical evidence and mutation sensitivity

- 278 deterministic full-digest differential cases on each of the interpreter and native C backend, compared with PyCryptodome Keccak-256.
- All lengths 0–273 cover every tail position and boundaries at 135/136/137 and 271/272/273.
- Dirty unused storage, 4 KiB and 64 KiB messages, and two invalid capacities.
- Empty input and `abc` known-answer examples distinguish Ethereum Keccak-256 from standardized SHA3-256.
- **All ten mutations are now rejected by the proof checker**: rotation, round constant, chi, digest order, capacity condition, suffix, actual final padding bit, input-word index, block count, and selected round count.

`build/validation.json` records the most recent complete validation. Mutation rejection requires a checker failure; timeouts are not counted as successful rejection.

## Trusted components

Bend 2.0.16's parser, termination/quantity checker and equality kernel; Base U32/Nat/Array semantics; native array lowering and other compiler passes; Clang; the platform runtime/CPU. C and PyCryptodome are independent empirical references, not axioms imported into the proofs. The project introduces no proof holes, unsafe recursion, FFI, or additional axioms. Emitted source from development generators is checked normally; generators are not proof oracles.
