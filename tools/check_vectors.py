from pathlib import Path
from Crypto.Hash import keccak
P=Path(__file__).resolve().parents[1]
cases=[(i,i+42) for i in range(274)]+[(4096,17),(65536,33)]
expected=[]
for n,seed in cases:
 data=b''.join(((i*2654435761+seed)&0xffffffff).to_bytes(4,'little') for i in range((n+3)//4))[:n]
 expected.append(keccak.new(digest_bits=256,data=data).hexdigest())
expected+=['invalid','invalid']
for name in ['vectors-js.txt','vectors-native.txt']:
 f=P/'build'/name
 if f.exists():
  got=f.read_text().splitlines();assert got==expected,[(i,x,y) for i,(x,y) in enumerate(zip(got,expected)) if x!=y][:3]
  print(name,':',len(expected),'passed')
