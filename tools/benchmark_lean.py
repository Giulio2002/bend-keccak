#!/usr/bin/env python3
"""Compare public Keccak-256 hashing in stock Bend, upstream Lean, and XKCP C."""
import hashlib,json,os,platform,statistics,subprocess,time
from pathlib import Path
from Crypto.Hash import keccak
P=Path(__file__).resolve().parents[1]
bins={'bend':P/'build/bench','lean':P/'build/lean/.lake/build/bin/keccakBench','xkcp':P/'build/xkcp'}

def data(n,seed=42):
    return b''.join(((i*2654435761+seed)&0xffffffff).to_bytes(4,'little') for i in range((n+3)//4))[:n]

def run(name,size,count):
    depth=max(0,(((size+3)//4)-1).bit_length())
    env={**os.environ,'KECCAK_SIZE':str(size),'KECCAK_DEPTH':str(depth),'KECCAK_COUNT':str(count)}
    cmd=[str(bins[name])]+(['--threads','1','--gpu','off'] if name=='bend' else [])
    out=subprocess.check_output(cmd,env=env,text=True,timeout=120).splitlines()
    digest=keccak.new(digest_bits=256,data=data(size)).digest()
    assert int(out[1])==(int.from_bytes(digest[:4],'little')*count)&0xffffffff,(name,size,out)
    if name=='lean':assert out[2]==digest.hex(),(name,size,out)
    return float(out[0].split('=',1)[1])

# Check full outputs, independently of timed checksums.
expected=[keccak.new(digest_bits=256,data=data(n,seed)).hexdigest()
          for n,seed in [(n,n+42) for n in range(274)]+[(4096,17),(65536,33)]]
lean_vectors=subprocess.check_output([str(bins['lean'])],env={**os.environ,'KECCAK_VECTORS':'1'},text=True,timeout=120).splitlines()
assert lean_vectors==expected,'Lean differential test failure'
bend_vectors=subprocess.check_output([str(P/'build/vectors'),'--threads','1','--gpu','off'],text=True,timeout=120).splitlines()
assert bend_vectors==expected+['invalid','invalid'],'Bend differential test failure'
print('Full digest checks: Lean 276, Bend 278 passed',flush=True)
record={'host':platform.platform(),'cpu':subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),
 'timestamp_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
 'bend_version':subprocess.check_output([str(Path.home()/'.bend/bin/bend'),'--version'],text=True).strip(),
 'bend_c_compiler':subprocess.check_output(['clang','--version'],text=True).splitlines()[0],
 'lean_build':json.loads((P/'build/lean/build-record.json').read_text()),
 'c_reference_commit':subprocess.check_output(['git','-C',str(P/'vendor/XKCP'),'rev-parse','HEAD'],text=True).strip(),
 'flags':['-O3','-march=native','-std=c11 (Bend/XKCP)'],
 'boundary':'Sequential repeated public hashes of prepared data. Bend consumes/clones its packed array; Lean reuses its immutable ByteArray; XKCP copies into preallocated scratch. Input generation, process startup, hex formatting, and validation excluded. Digest allocation and checksum included. Counts calibrated per implementation for timer resolution.',
 'samples':5,'warmups':1,'target_batch_ms':250,
 'validation':{'lean_full_digests':276,'bend_cases':278,'timed_checksums':'all samples checked against PyCryptodome Keccak'},
 'binary_sha256':{k:hashlib.sha256(v.read_bytes()).hexdigest() for k,v in bins.items()},
 'production_sha256':{str(f.relative_to(P)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (P/'src').glob('*.bend')},'rows':[]}
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
        names=list(bins)
        # Rotate order so each participant appears at different positions.
        names=names[repeat%3:]+names[:repeat%3]
        for name in names:samples[name].append(run(name,size,counts[name]))
    us={n:statistics.median(v)*1000/counts[n] for n,v in samples.items()}
    row={'bytes':size,'counts':counts,'samples_ms':samples,'us_per_hash':us,'lean_over_bend':us['lean']/us['bend'],'bend_over_c':us['bend']/us['xkcp']}
    record['rows'].append(row)
    (P/'benchmarks/lean-comparison-arm64.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps(row),flush=True)
