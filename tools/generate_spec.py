# Emit a coordinate-based specification. Imports only Base and the neutral types.
from pathlib import Path
P=Path(__file__).resolve().parents[1]
s='import Base\nimport ../src/types.bend as T\n\n'
s+='''# 64-bit lanes are specified by two 32-bit halves, low half first.
def xor(a: T.Lane, b: T.Lane) -> T.Lane:
  match a b:
    case T.W{al,ah} T.W{bl,bh}: T.W{U32.xor(al,bl),U32.xor(ah,bh)}

def chi(a: T.Lane, b: T.Lane, c: T.Lane) -> T.Lane:
  match a b c:
    case T.W{al,ah} T.W{bl,bh} T.W{cl,ch}:
      T.W{U32.xor(al,U32.and(U32.xor(bl,4294967295),cl)),U32.xor(ah,U32.and(U32.xor(bh,4294967295),ch))}

def rotate_small(+lo: U32, +hi: U32, +n: Nat) -> T.Lane:
  T.W{U32.or(U32.shln(lo,n),U32.shrn(hi,Nat.sub(32n,n))),U32.or(U32.shln(hi,n),U32.shrn(lo,Nat.sub(32n,n)))}

def rotate_nonzero(lo: U32, hi: U32, +n: Nat, b: Bool) -> T.Lane:
  match b:
    case True{}: rotate_small(lo,hi,n)
    case False{}: rotate_small(hi,lo,Nat.sub(n,32n))

def rotate(a: T.Lane, +n: Nat) -> T.Lane:
  match a n:
    case T.W{lo,hi} 0n: T.W{lo,hi}
    case T.W{lo,hi} 32n: T.W{hi,lo}
    case T.W{lo,hi} n: rotate_nonzero(lo,hi,n,Nat.is_lt(n,32n))

'''
# Read-only coordinate observation on the mathematical fixed state.
s+='def at(s: T.State, i: Nat) -> T.Lane:\n  match s i:\n'
for i in range(25):s+='    case T.S{'+','.join(f'a{j}' for j in range(25))+f'}} {i}n: a{i}\n'
s+='    case _ _: T.W{0,0}\n\ndef column(+s: T.State, +x: Nat) -> T.Lane:\n  xor(at(s,x),xor(at(s,Nat.add(x,5n)),xor(at(s,Nat.add(x,10n)),xor(at(s,Nat.add(x,15n)),at(s,Nat.add(x,20n))))))\n\ndef theta_lane(+s: T.State, +x: Nat, y: Nat) -> T.Lane:\n  xor(at(s,Nat.add(x,Nat.mul(5n,y))),xor(column(s,Nat.mod(Nat.add(x,4n),5n)),rotate(column(s,Nat.mod(Nat.add(x,1n),5n)),1n)))\n'
s+='\ndef theta(+s: T.State) -> T.State:\n  T.S{'+','.join(f'theta_lane(s,{x}n,{y}n)' for y in range(5) for x in range(5))+'}\n'
# Derive rho offsets by Keccak coordinate recurrence rather than runtime table.
rho={(0,0):0};x,y=1,0
for t in range(24):rho[x,y]=((t+1)*(t+2)//2)%64;x,y=y,(2*x+3*y)%5
s+='\ndef rho_pi(+s: T.State) -> T.State:\n  T.S{'
v={}
for (x,y),r in rho.items():v[y, (2*x+3*y)%5]=f'rotate(at(s,{x+5*y}n),{r}n)'
s+=','.join(v[x,y] for y in range(5) for x in range(5))+'}\n\ndef chi_state(+s: T.State) -> T.State:\n  T.S{'+','.join(f'chi(at(s,{x+5*y}n),at(s,{(x+1)%5+5*y}n),at(s,{(x+2)%5+5*y}n))' for y in range(5) for x in range(5))+'}\n'
s+='\ndef iota(s: T.State, rc: T.Lane) -> T.State:\n  match s:\n    case T.S{'+','.join(f'a{i}' for i in range(25))+'}:\n      T.S{xor(a0,rc),'+','.join(f'a{i}' for i in range(1,25))+'}\n\ndef round(s: T.State, rc: T.Lane) -> T.State:\n  iota(chi_state(rho_pi(theta(s))),rc)\n'
# Independent round constants calculated with the reference LFSR.
r=1;constants=[]
for i in range(24):
 c=0
 for j in range(7):
  if r&1:c ^= 1<<((1<<j)-1)
  r=((r<<1)^ (0x71 if r&0x80 else 0)) &255
 constants.append(c)
s+='\ndef constant(i: Nat) -> T.Lane:\n  match i:\n'
for i,r in enumerate(constants):s+=f'    case {i}n: T.W{{{r&0xffffffff},{r>>32}}}\n'
s+='    case _: T.W{0,0}\n\ndef rounds(n: Nat, +i: Nat, s: T.State) -> T.State:\n  match n:\n    case 0n: s\n    case 1n+p: rounds(p,1n+i,round(s,constant(i)))\n\ndef permute(s: T.State) -> T.State:\n  rounds(24n,0n,s)\n'
(P/'spec/permutation.bend').write_text(s)
