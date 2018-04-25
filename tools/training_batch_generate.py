
# Python3 compatible

import os
import subprocess

rootdir = os.path.abspath(os.path.join(__file__, "..", ".."))

multiprocess_reference_py = os.path.join(rootdir, "tools", "multiprocess_reference.py")

TASK_LIST = [

    "/home/gj/git/pbrt-v3-scenes/measure-one/frame120.pbrt",
    "/home/gj/git/pbrt-v3-scenes/pbrt-book/book.pbrt",
    "/home/gj/git/pbrt-v3-scenes/killeroos/killeroo-gold.pbrt",
    "/home/gj/git/pbrt-v3-scenes/sanmiguel/sanmiguel.pbrt",
    "/home/gj/git/pbrt-v3-scenes/sportscar/sportscar.pbrt",
    "/home/gj/git/pbrt-v3-scenes/structuresynth/arcsphere.pbrt"

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
