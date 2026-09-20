from pathlib import Path
import subprocess
P=Path(__file__).resolve().parents[1]
COMMIT='eb5244d6b95fb1c434b211bac293093e18aa8fd1'
v=P/'vendor/XKCP'
if not v.exists():
 v.parent.mkdir(exist_ok=True);subprocess.run(['git','clone','https://github.com/XKCP/XKCP.git',str(v)],check=True)
if subprocess.check_output(['git','-C',str(v),'rev-parse','HEAD'],text=True).strip()!=COMMIT:
 if subprocess.check_output(['git','-C',str(v),'status','--porcelain'],text=True).strip():raise SystemExit('Reference checkout has changes; refusing to overwrite.')
 subprocess.run(['git','-C',str(v),'checkout','--detach',COMMIT],check=True)
subprocess.run(['git','-C',str(v),'diff','--exit-code','HEAD','--','lib'],check=True)
print(COMMIT)
