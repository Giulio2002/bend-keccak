#!/usr/bin/env python3
"""Keccak-256 per hash on a Linux host: Bend (build/bench), XKCP's optimized and
compact portable C, and optionally a previous Bend build (--previous BINARY).

Bend binaries are built plainly (`bend benchmarks/driver.bend -o build/bench`);
C by tools/build_c.py. Binaries may be built on another host (--compiler records
which clang). Pass --cpu N to pin every run to one core with taskset."""
import argparse,hashlib,json,os,platform,statistics,subprocess,time
from pathlib import Path
from Crypto.Hash import keccak
P=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser();ap.add_argument('--cpu',type=int);ap.add_argument('--previous');ap.add_argument('--out',default='benchmarks/results-x86_64.json');ap.add_argument('--compiler',help='compiler the binaries were built with, when built on another host');args=ap.parse_args()
bins={'bend':P/'build/bench','c_optimized':P/'build/xkcp','c_portable':P/'build/xkcp-compact'}
if args.previous:bins['bend_previous']=Path(args.previous)

def data(n,seed=42):
    return b''.join(((i*2654435761+seed)&0xffffffff).to_bytes(4,'little') for i in range((n+3)//4))[:n]

def run(name,size,count):
    depth=max(0,(((size+3)//4)-1).bit_length())
    env={**os.environ,'KECCAK_SIZE':str(size),'KECCAK_DEPTH':str(depth),'KECCAK_COUNT':str(count)}
    bend=name.startswith('bend')
    cmd=(['taskset','-c',str(args.cpu)] if args.cpu is not None else [])+[str(bins[name])]+(['--threads','1','--gpu','off'] if bend else [])
    out=subprocess.check_output(cmd,env=env,text=True,timeout=600).splitlines()
    digest=keccak.new(digest_bits=256,data=data(size)).digest()
    assert int(out[1])==(int.from_bytes(digest[:4],'little')*count)&0xffffffff,(name,size,out)
    if not bend:assert out[2]==digest.hex(),(name,size,out)
    return float(out[0].split('=',1)[1])

cpu=next((l.split(':',1)[1].strip() for l in open('/proc/cpuinfo') if l.startswith('model name')),platform.processor())
record={'host':platform.platform(),'cpu':cpu,'pinned_cpu':args.cpu,'load_average':os.getloadavg(),
 'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
 'compiler':args.compiler or subprocess.check_output(['clang','--version'],text=True).splitlines()[0],
 'builds':{'bend':'bend benchmarks/driver.bend -o build/bench','c':'clang -O3 -march=native -std=c11 (tools/build_c.py)'},
 'boundary':'Sequential repeated public hashes of prepared data; input generation, startup and validation excluded. Bend clones its consumed input per hash; C copies into preallocated scratch. Digest checksums checked against PyCryptodome Keccak.',
 'samples':5,'target_batch_ms':250,
 'binary_sha256':{k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in bins.items()},'rows':[]}
for size in [0,32,64,135,136,137,1024,16384,65536,1048576]:
    counts={}
    for name in bins:
        count=1;ms=run(name,size,count)
        while ms<2 and count<1048576:
            count=min(1048576,count*64);ms=run(name,size,count)
        counts[name]=max(1,min(1048576,round(count*250/max(ms,0.001))))
        run(name,size,counts[name])
    samples={n:[] for n in bins}
    for repeat in range(5):
        names=list(bins);names=names[repeat%len(names):]+names[:repeat%len(names)]
        for name in names:samples[name].append(run(name,size,counts[name]))
    us={n:statistics.median(v)*1000/counts[n] for n,v in samples.items()}
    row={'bytes':size,'counts':counts,'samples_ms':samples,'us_per_hash':us,'bend_over_c':us['bend']/us['c_optimized']}
    if 'bend_previous' in us:row['previous_over_bend']=us['bend_previous']/us['bend']
    record['rows'].append(row)
    (P/args.out).write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({'bytes':size,'us':{k:round(v,3) for k,v in us.items()}}),flush=True)
