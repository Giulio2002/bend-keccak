import KeccakEngine.Spec

-- Benchmark-only binding to exactly the runtime implementation selected by
-- upstream Core.lean's @[implemented_by Spec.keccakF1600]. The upstream proof
-- chain is not rebuilt by this harness; no proof claim is made about this shim.
namespace KeccakEngine
@[inline] def keccakF1600_core (state : Array (BitVec 64)) : Array (BitVec 64) :=
  Spec.keccakF1600 state
end KeccakEngine
