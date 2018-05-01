
# Python3 compatible

import os
import subprocess

rootdir = os.path.abspath(os.path.join(__file__, "..", ".."))

multiprocess_reference_py = os.path.join(rootdir, "tools", "multiprocess_reference.py")

TASK_LIST = [
    "/home/gj/git/pbrt-v3-scenes/villa/villa-lights-on.pbrt",
    "/home/gj/git/pbrt-v3-scenes/white-room/whiteroom-night.pbrt",
    "/home/gj/git/pbrt-v3-scenes/measure-one/frame35.pbrt",
    "/home/gj/git/pbrt-v3-scenes/sanmiguel/sanmiguel_cam3.pbrt",
    "/home/gj/git/pbrt-v3-scenes-extra/kitchen/scene.pbrt",
    "/home/gj/git/pbrt-v3-scenes-extra/living-room/scene.pbrt",
    "/home/gj/git/pbrt-v3-scenes-extra/living-room-3/scene.pbrt"
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
    cmd.append("--reference_samples=1024")

    print("Executing cmd {}".format(cmd))
    subprocess.call(cmd)
