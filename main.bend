import Base
import ./src/keccak.bend as K
import ./src/hex.bend as H

def show(r: Maybe<&1,Array<U32>>) -> String:
  match r:
    case None{}: "invalid"
    case Some{a}: H.hex(a)

def main() -> IO(Unit):
  do IO<Unit>:
    IO.print(show(K.keccak256(Array.new(U32,0n,0),0n)))
    IO.print(show(K.keccak256(Array.new(U32,0n,6513249),3n)))
