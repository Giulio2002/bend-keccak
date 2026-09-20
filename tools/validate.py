#!/usr/bin/env python3
import argparse,json,os,re,shutil,subprocess,tempfile,time
from pathlib import Path
from Crypto.Hash import keccak
P=Path(__file__).resolve().parents[1];B=os.environ.get('BEND',str(Path.home()/'.bend/bin/bend'))
def run(args,cwd=P,timeout=120):
 r=subprocess.run([str(x) for x in args],cwd=cwd,capture_output=True,text=True,timeout=timeout)
 if r.returncode:raise RuntimeError(f'{args}: {r.stdout[:1000]}\n{r.stderr[:1000]}')
 return r.stdout

def audit():
 for f in (P/'src').glob('*.bend'):
  s='\n'.join(x.split('#')[0] for x in f.read_text().splitlines())
  assert not re.search(r'\b(List|Nil|Cons)\b|@unsafe|\?\w+|import\s+[\"]',s),f
  assert '/spec/' not in s and '/proofs/' not in s,f
 spec=(P/'spec/permutation.bend').read_text()
 assert re.findall(r'^import (.+)$',spec,re.M)==['Base','../src/types.bend as T']
 sponge=(P/'spec/sponge.bend').read_text()
 assert re.findall(r'^import (.+)$',sponge,re.M)==['Base','../src/types.bend as T','./permutation.bend as F']
 for f in [*(P/'src').glob('*.bend'),*(P/'proofs').glob('*.bend'),*(P/'spec').glob('*.bend')]:
  assert not re.search(r'@unsafe|\?\w+',f.read_text()),f

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--mutations',action='store_true');args=parser.parse_args();(P/'build').mkdir(exist_ok=True);audit();report={}
 start=time.monotonic();out=run([B,'PROOF.bend']);assert 'All terms check.' in out;report['proof_seconds']=time.monotonic()-start;print('Public sponge and component laws: checked',flush=True)
 for backend in ['js','native']:
  if backend=='js':out=run([B,'tests/vectors.bend'])
  else:
   run([B,'tests/vectors.bend','-o','build/vectors.c']);run(['clang','-O3','-march=native','-std=c11','build/vectors.c','-lpthread','-lm','-o','build/vectors']);out=run(['build/vectors','--threads','1','--gpu','off'])
  expected=[]
  for n,seed in [(i,i+42) for i in range(274)]+[(4096,17),(65536,33)]:
   data=b''.join(((i*2654435761+seed)&0xffffffff).to_bytes(4,'little') for i in range((n+3)//4))[:n];expected.append(keccak.new(digest_bits=256,data=data).hexdigest())
  expected+=['invalid','invalid'];assert out.splitlines()==expected,backend
  (P/'build'/f'vectors-{backend}.txt').write_text(out);report[backend+'_cases']=len(expected);print(backend,len(expected),'passed',flush=True)
 if args.mutations:
  mutations=[
   ('rotation','src/lane.bend','U32.shln(lo,12n)','U32.shln(lo,11n)','proof'),
   ('constant','src/permutation.bend','case 0n: T.W{1,0}','case 0n: T.W{2,0}','proof'),
   ('chi','src/lane.bend','U32.xor(bl,4294967295)','U32.xor(bl,4294967294)','proof'),
   ('digest_order','src/keccak.bend','Array.set(U32,a,0,l0)','Array.set(U32,a,0,h0)','proof'),
   ('capacity','src/keccak.bend','Nat.is_le(length,Nat.mul','Nat.is_ge(length,Nat.mul','proof'),
   ('partial_suffix','src/keccak.bend','case 0n: 1','case 0n: 2','proof'),
   ('final_padding_bit','src/keccak.bend','U32.or(pad_word(w33,132n,remain),2147483648)','U32.or(pad_word(w33,132n,remain),1073741824)','proof')]
  mutations += [
   ('block_word_index','src/keccak.bend','Array.get(U32,a,U32.add(index,33))','Array.get(U32,a,U32.add(index,32))','proof'),
   ('block_count','src/keccak.bend','Nat.div(length,136n)','Nat.div(length,135n)','proof'),
   ('selected_round_count','src/keccak.bend','keccak256_rounds(24n,a,length)','keccak256_rounds(23n,a,length)','proof')]
  report['mutations']=[]
  for name,file,old,new,mode in mutations:
   with tempfile.TemporaryDirectory(prefix='keccak-mutation-') as d:
    q=Path(d)
    for folder in ['src','spec','proofs']:shutil.copytree(P/folder,q/folder)
    for f in ['PROOF.bend','LAWS.bend','main.bend']:shutil.copy(P/f,q/f)
    f=q/file;s=f.read_text();assert old in s,(name,old);f.write_text(s.replace(old,new,1))
    r=subprocess.run([B,'PROOF.bend' if mode=='proof' else 'main.bend'],cwd=q,capture_output=True,text=True,timeout=120)
    if mode=='proof':assert r.returncode!=0 and 'expected' in r.stderr+r.stdout,(name,r.stdout[:500],r.stderr[:500])
    else:assert r.returncode==0 and r.stdout.splitlines()[0]!='c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
    report['mutations'].append({'name':name,'rejected_by':mode});print('Mutation rejected:',name,mode,flush=True)
 (P/'build/validation.json').write_text(json.dumps(report,indent=2))
if __name__=='__main__':main()
