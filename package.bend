# bend-keccak: pure stock-Bend Ethereum Keccak-256. MIT licensed.
# https://github.com/Giulio2002/bend-keccak
# This entry checks and bundles the complete public sponge refinement proof.
# Use keccak.bend from the same package for runtime-only imports.
# Input: four little-endian bytes per U32, plus logical byte length.
# Output: Some{eight little-endian U32 words}, exactly 32 digest bytes;
# None if logical length exceeds input capacity. Input is consumed.
# Proof: universal public packed-array API refinement to the independent packed
# sponge specification, including padding, absorption, rejection, and all words.
# Not a proof of cryptographic security, constant-time execution, the compiler,
# or hardware. Kernel, Base, compiler, native toolchain and CPU remain trusted.
# Full statement and limits: repository CORRECTNESS.md.
import Base
import ./keccak.bend as K
import ./PROOF.bend as Proof

def keccak256(words: Array<U32>, byte_length: Nat) -> Maybe<&1,Array<U32>>:
  K.keccak256(words,byte_length)

def hex(digest: Array<U32>) -> String:
  K.hex(digest)
