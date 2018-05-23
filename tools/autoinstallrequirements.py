import os
import sys
import subprocess
import time

def run_required(cmd):
    print(">>> {}".format(" ".join(cmd)))
    code = subprocess.call(cmd, shell=False)
    if code != 0:
        print("Error, command {} exited with {}".format(cmd, code))
        sys.exit(1)

run_required(["apt", "update"])

run_required(["apt", "install", "libgconf-2-4"])

print("By proceeding you agree to the miniconda license agreement! Press ENTER to continue")
input()

minicondaUrl = "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh"

os.chdir("/tmp")

run_required(["wget", "-O", "miniconda.sh", minicondaUrl])

run_required(["chmod", "+x", "miniconda.sh"])

homeDir = os.path.expanduser("~")

minicondaDir = os.path.join(homeDir, "miniconda")

minicondaBinDir = os.path.join(minicondaDir, "bin")

# Install miniconda

run_required([
    "/tmp/miniconda.sh",
    "-b",
    "-p",
    minicondaDir
])

# Add to .profile

profilePath = os.path.join(homeDir, ".profile")

def fileContainsString(fpath, s):
    res = False
    f = open(fpath, "r")
    for line in f:
        line = line.strip()
        if s in line:
            res = True
            break
    f.close()
    return res

def fileAppendString(fpath, s):
    f = open(fpath, "a")
    f.write("\n{}\n".format(s))
    f.close()

# Check if it's not already contained
if not fileContainsString(profilePath, minicondaBinDir):
    fileAppendString(profilePath, 'export PATH="{}:$PATH"'.format(minicondaBinDir))

print("Updated {}".format(profilePath))

env = os.environ
envPath = env["PATH"]
envPath = minicondaBinDir + ":" + envPath
env["PATH"] = envPath

# Install items using conda

condaExec = os.path.join(minicondaBinDir, "conda")

# conda install pytorch-cpu torchvision-cpu -c pytorch
subprocess.call([
    condaExec, 
    "install",
    "pytorch-cpu",
    "torchvision-cpu",
    "-c", 
    "pytorch"
], env=env)


print("Installation complete. Please LOGOUT and log back in for the environment to take effect")
time.sleep(2)
print("Press ENTER to finish")
input()