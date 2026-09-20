from pathlib import Path
import subprocess,os,json,statistics,platform,hashlib
from Crypto.Hash import keccak
P=Path(__file__).resolve().parents[1]
results={'host':platform.platform(),'bend':subprocess.check_output([str(Path.home()/'.bend/bin/bend'),'--version'],text=True).strip(),'compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],'flags':['-O3','-march=native','-std=c11'],'reference_commit':subprocess.check_output(['git','-C',str(P/'vendor/XKCP'),'rev-parse','HEAD'],text=True).strip(),'warmups':1,'samples':5,'boundary':'Repeated public hashes, input preparation excluded; packed input clone included in Bend, memcpy into preallocated scratch included in C. Digest checksum retained.','rows':[]}
results['binary_sha256']={name:hashlib.sha256((P/'build'/name).read_bytes()).hexdigest() for name in ['bench','xkcp']}
results['production_sha256']={str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/'src').glob('*.bend')}
for size in [0,32,64,135,136,137,1024,16384,65536,1048576]:
 depth=max(0,(((size+3)//4)-1).bit_length());cap=(1<<depth)*4;count=max(64,min(524288,64*1024*1024//max(1,size)))
 data=b''.join(((i*2654435761+42)&0xffffffff).to_bytes(4,'little') for i in range(cap//4))[:size]
 expected=(int.from_bytes(keccak.new(digest_bits=256,data=data).digest()[:4],'little')*count)&0xffffffff
 env={**os.environ,'KECCAK_SIZE':str(size),'KECCAK_DEPTH':str(depth),'KECCAK_COUNT':str(count)}
 def run(name):
  cmd=[str(P/'build'/('bench' if name=='bend' else 'xkcp'))]
  if name=='bend':cmd+=['--threads','1','--gpu','off']
  r=subprocess.run(cmd,env=env,text=True,capture_output=True,check=True,timeout=120);lines=r.stdout.splitlines();assert int(lines[1])==expected,(size,name,lines,expected)
  return float(lines[0].split('=')[1])
 samples={'bend':[],'xkcp':[]}
 for name in samples:run(name)
 for i in range(5):
  for name in (list(samples) if i%2==0 else list(samples)[::-1]):samples[name].append(run(name))
 med={n:statistics.median(v)*1000/count for n,v in samples.items()}
 row={'bytes':size,'count':count,'samples_ms':samples,'us_per_hash':med,'ratio':med['bend']/med['xkcp'],'checksum_verified':True};results['rows'].append(row);print(row,flush=True)
 (P/'benchmarks/results-arm64.json').write_text(json.dumps(results,indent=2))
