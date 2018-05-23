import os
import sys
import subprocess

minicondaUrl = "https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh"

os.chdir("/tmp")

subprocess.call(["wget", "-O", "miniconda.sh", minicondaUrl])

subprocess.call(["chmod", "+x", "miniconda.sh"])

homeDir = os.path.expanduser("~")

minicondaDir = os.path.join(homeDir, "miniconda")

minicondaBinDir = os.path.join(minicondaDir, "bin")

# Install miniconda

subprocess.call([
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


print("Installation complete. Your new environment will take effect after a new login or new terminal")