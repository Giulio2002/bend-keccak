from pathlib import Path
import os,subprocess,statistics,json
P=Path(__file__).resolve().parents[1];rows=[]
for size,depth,count in [(64,4,262144),(1024,8,65536),(65536,14,1024),(1048576,18,64)]:
 env={**os.environ,'KECCAK_SIZE':str(size),'KECCAK_DEPTH':str(depth),'KECCAK_COUNT':str(count)}
 def run(n):
  out=subprocess.check_output([str(P/'build'/n),'--threads','1','--gpu','off'],env=env,text=True).splitlines();return float(out[0].split('=')[1]),out[1]
 samples={'baseline':[],'bench':[]};expected=run('baseline')[1]
 assert run('bench')[1]==expected
 for i in range(7):
  for n in (['baseline','bench'] if i%2==0 else ['bench','baseline']):
   ms,chk=run(n);assert chk==expected;samples[n].append(ms)
 med={n:statistics.median(v) for n,v in samples.items()};row={'bytes':size,'iterations':count,'samples_ms':samples,'speedup':med['baseline']/med['bench']};rows.append(row);print(row,flush=True)
(P/'benchmarks/scheduling-experiment.json').write_text(json.dumps(rows,indent=2))
