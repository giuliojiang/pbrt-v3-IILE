import sys
import subprocess
import os
import time

NO_PROCESSES = 4

argv = sys.argv[1:]

rootdir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

cmd = []
cmd.append(os.path.join(rootdir, "bin", "pbrt"))
for arg in argv:
    cmd.append(arg)
print("full cmd is {}".format(cmd))

procs = []

print("STARTING {} PROCESSES".format(NO_PROCESSES))

for i in range(NO_PROCESSES):
    envv = {
        "IISPT_REFERENCE_CONTROL_MOD": str(NO_PROCESSES),
        "IISPT_REFERENCE_CONTROL_MATCH": str(i)
    }
    a_proc = subprocess.Popen(cmd, env=envv)
    procs.append(a_proc)
    time.sleep(5)

for p in procs:
    p.wait()