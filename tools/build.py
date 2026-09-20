from pathlib import Path
import os,subprocess
P=Path(__file__).resolve().parents[1];B=os.environ.get('BEND',str(Path.home()/'.bend/bin/bend'));(P/'build').mkdir(exist_ok=True)
for name,source in [('main','main.bend'),('bench','benchmarks/driver.bend')]:
 subprocess.run([B,source,'-o',f'build/{name}.c'],cwd=P,check=True)
 subprocess.run(['clang','-O3','-march=native','-std=c11',f'build/{name}.c','-lpthread','-lm','-o',f'build/{name}'],cwd=P,check=True)
subprocess.run(['python3','tools/fetch_reference.py'],cwd=P,check=True)
subprocess.run(['python3','tools/build_c.py'],cwd=P,check=True)
