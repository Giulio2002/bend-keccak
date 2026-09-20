#!/usr/bin/env python3
"""Build the pinned upstream Lean runtime path, without rebuilding its proof chain."""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path
P = Path(__file__).resolve().parents[1]
COMMIT = '053b9ddee2084332e0a7b25800bca9d4f56ffa8d'
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--lake', default=os.environ.get('LAKE', 'lake'))
a = p.parse_args()
upstream = P/'vendor/lean-keccak'
if not upstream.exists():
    subprocess.run(['git','clone','https://github.com/AlexeyMilovanov/lean-keccak-unrolled.git',str(upstream)],check=True)
subprocess.run(['git','-C',str(upstream),'checkout','--detach',COMMIT],check=True)
subprocess.run(['git','-C',str(upstream),'diff','--exit-code',COMMIT,'--','KeccakEngine'],check=True)
out = P/'build/lean'; (out/'KeccakEngine').mkdir(parents=True, exist_ok=True)
for name in ['Spec.lean','Sponge.lean']:
    shutil.copyfile(upstream/'KeccakEngine'/name,out/'KeccakEngine'/name)
shutil.copyfile(P/'benchmarks/lean/Core.lean',out/'KeccakEngine/Core.lean')
shutil.copyfile(P/'benchmarks/lean/Bench.lean',out/'Bench.lean')
shutil.copyfile(upstream/'lean-toolchain',out/'lean-toolchain')
(out/'lakefile.toml').write_text('''name = "keccak-runtime-benchmark"
version = "0.1.0"
moreLeancArgs = ["-O3", "-march=native"]
[[lean_lib]]
name = "KeccakEngine"
[[lean_exe]]
name = "keccakBench"
root = "Bench"
''')
subprocess.run([a.lake,'build','keccakBench'],cwd=out,check=True)
prefix = Path(subprocess.check_output([a.lake,'env','lean','--print-prefix'],cwd=out,text=True).strip())
compiler_version = subprocess.check_output([str(prefix/'bin/clang'),'--version'],text=True).splitlines()[0]
record = {'upstream': 'https://github.com/AlexeyMilovanov/lean-keccak-unrolled', 'commit': COMMIT,
 'lean_version':subprocess.check_output([a.lake,'env','lean','--version'],cwd=out,text=True).strip(),
 'compiler':compiler_version,
 'compiler_command':json.loads((out/'.lake/build/ir/KeccakEngine/Spec.c.o.export.trace').read_text())['log'][0]['message'],
 'flags':['-O3','-march=native'], 'proof_chain_rebuilt':False,
 'runtime_binding':'Benchmark shim calls Spec.keccakF1600, the exact target of upstream Core implemented_by. Spec.lean and Sponge.lean copied byte-for-byte.',
 'files':{str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [out/'KeccakEngine/Spec.lean',out/'KeccakEngine/Sponge.lean',out/'KeccakEngine/Core.lean',out/'Bench.lean']}}
(out/'build-record.json').write_text(json.dumps(record,indent=2)+'\n')
print(out/'.lake/build/bin/keccakBench')
