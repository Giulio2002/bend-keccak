import Base
import ./src/types.bend as T
import ./src/permutation.bend as P
import ./spec/permutation.bend as S
import ./src/keccak.bend as K
import ./spec/sponge.bend as Sponge
import ./spec/interleave.bend as I
import ./src/lane.bend as L

# Universal permutation refinement; instantiating n=24 and i=0 gives Keccak-f[1600].
law permutation_rounds:
  for +n: Nat
  for +i: Nat
  for +s: T.State
  {P.rounds(n,i,s) == S.rounds(n,i,s) : T.State}

law digest_size:
  for s: T.State
  {Pair.snd(Array<U32>,U32,Array.size(U32,K.digest(s))) == 8 : U32}

law capacity_rejection:
  for a: Array<U32>
  for +n: Nat
  for +capacity: U32
  for invalid: {Nat.is_le(n,Nat.mul(4n,U32.to_nat(capacity))) == False{} : Bool}
  {K.sized(24n,n,(a,capacity)) == None{} : Maybe<&1,Array<U32>>}

law packed_sponge_correct:
  for +r: Nat
  for a: Array<U32>
  for +length: Nat
  {K.keccak256_rounds(r,a,length) == Sponge.keccak256_rounds(r,a,length) : Maybe<&1,Array<U32>>}

law ethereum_round_count:
  for a: Array<U32>
  for +length: Nat
  {K.keccak256(a,length) == K.keccak256_rounds(24n,a,length) : Maybe<&1,Array<U32>>}

law ethereum_keccak256:
  for a: Array<U32>
  for +length: Nat
  {K.keccak256(a,length) == Sponge.keccak256_rounds(24n,a,length) : Maybe<&1,Array<U32>>}

# The interleaved permutation that K.keccak256 runs acts on the interleaved
# form of every state as the specification permutation does, for every
# round count and starting round.
law interleaved_permutation:
  for +n: Nat
  for +i: Nat
  for +s: T.State
  {P.steps(n,i,I.interleave(s)) == I.interleave(S.rounds(n,i,s)) : T.St}

# Interleaving a lane's two input words (as the absorb does) and taking the
# lane back out (as the squeeze does) gives the lane.
law interleave_roundtrip:
  for +lo: U32
  for +hi: U32
  {T.W{L.low(L.even(L.unz(lo),L.unz(hi)),L.odd(L.unz(lo),L.unz(hi))),L.high(L.even(L.unz(lo),L.unz(hi)),L.odd(L.unz(lo),L.unz(hi)))} == T.W{lo,hi} : T.Lane}
