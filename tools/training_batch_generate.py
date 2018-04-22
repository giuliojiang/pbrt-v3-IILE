
# Python3 compatible

import os
import subprocess

rootdir = os.path.abspath(os.path.join(__file__, "..", ".."))

multiprocess_reference_py = os.path.join(rootdir, "tools", "multiprocess_reference.py")

TASK_LIST = [

    "/home/gj/git/pbrt-v3-scenes/barcelona-pavilion/pavilion-night.pbrt",
    "/home/gj/git/pbrt-v3-scenes/breakfast/breakfast.pbrt",
    "/home/gj/git/pbrt-v3-scenes/buddha-fractal/buddha-fractal.pbrt",
    "/home/gj/git/pbrt-v3-scenes/chopper-titan/chopper-titan.pbrt",
    "/home/gj/git/pbrt-v3-scenes/crown/crown.pbrt"

]

for task in TASK_LIST:

    taskdir = os.path.dirname(task)
    print("Changing directory to {}".format(taskdir))
    os.chdir(taskdir)

    cmd = []
    cmd.append("python3")
    cmd.append(multiprocess_reference_py)
    cmd.append(task)
    cmd.append("--reference=20")

    print("Executing cmd {}".format(cmd))
    subprocess.call(cmd)
