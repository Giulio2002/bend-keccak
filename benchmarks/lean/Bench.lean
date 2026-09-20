import KeccakEngine.Sponge

private def input (n : Nat) (seed : UInt32 := 42) : ByteArray := Id.run do
  let mut a := ByteArray.emptyWithCapacity n
  for i in [:n] do
    let w := UInt32.ofNat (i / 4) * 2654435761 + seed
    a := a.push ((w >>> UInt32.ofNat (8 * (i % 4))).toUInt8)
  return a

private def hex (a : ByteArray) : String := Id.run do
  let digits := "0123456789abcdef".toList.toArray
  let mut s := ""
  for b in a do
    s := s.push digits[b.toNat / 16]!
    s := s.push digits[b.toNat % 16]!
  return s

private def number (key : String) : IO Nat := do
  let some text ← IO.getEnv key | throw (IO.userError s!"missing {key}")
  let some n := text.toNat? | throw (IO.userError s!"invalid {key}")
  return n

-- Keep the per-hash call visible when inspecting the compiled benchmark loop.
@[noinline] private def hashOnce (data : ByteArray) : ByteArray :=
  KeccakEngine.keccak256 data

def main : IO Unit := do
  if (← IO.getEnv "KECCAK_VECTORS") == some "1" then
    for n in [:274] do
      IO.println (hex (hashOnce (input n (UInt32.ofNat (n + 42)))))
    for (n, seed) in [(4096, 17), (65536, 33)] do
      IO.println (hex (hashOnce (input n seed)))
    return
  let size ← number "KECCAK_SIZE"
  let count ← number "KECCAK_COUNT"
  let data := input size
  let start ← IO.monoNanosNow
  let mut checksum : UInt32 := 0
  for _ in [:count] do
    let d := hashOnce data
    let w := d[0]!.toUInt32 ||| (d[1]!.toUInt32 <<< 8) |||
             (d[2]!.toUInt32 <<< 16) ||| (d[3]!.toUInt32 <<< 24)
    checksum := checksum + w
  let stop ← IO.monoNanosNow
  IO.println s!"BENCH_MS={(stop - start).toFloat / 1000000.0}"
  IO.println checksum
  IO.println (hex (hashOnce data))
