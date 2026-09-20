from pathlib import Path
import subprocess,json
P=Path(__file__).resolve().parents[1];v=P/'vendor/XKCP';(P/'build/config.h').write_text('/* Use upstream default fully-unrolled portable C configuration. */\n')
incs=['vendor/XKCP/lib/low/common','build','vendor/XKCP/lib/common','vendor/XKCP/lib/low/KeccakP-1600/common','vendor/XKCP/lib/low/KeccakP-1600/plain-64bits','vendor/XKCP/lib/low/KeccakP-1600/plain-64bits/SnP']
cmd=['clang','-O3','-march=native','-std=c11',*[f'-I{x}' for x in incs],'benchmarks/xkcp.c','vendor/XKCP/lib/low/KeccakP-1600/plain-64bits/KeccakP-1600-opt64.c','-o','build/xkcp']
subprocess.run(cmd,cwd=P,check=True);(P/'build/c-command.json').write_text(json.dumps(cmd,indent=2))
# A distinct compact portable reference, at the same optimization level.
compact_incs=['build','vendor/XKCP/lib/common','vendor/XKCP/lib/low/common','vendor/XKCP/lib/low/KeccakP-1600/common','vendor/XKCP/lib/low/KeccakP-1600/compact']
compact_cmd=['clang','-O3','-march=native','-std=c11',*[f'-I{x}' for x in compact_incs],'benchmarks/xkcp.c','vendor/XKCP/lib/low/KeccakP-1600/compact/KeccakP-1600-compact64.c','-o','build/xkcp-compact']
subprocess.run(compact_cmd,cwd=P,check=True)
(P/'build/c-compact-command.json').write_text(json.dumps(compact_cmd,indent=2))
