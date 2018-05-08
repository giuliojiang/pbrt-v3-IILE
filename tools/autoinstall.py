import os
import sys
import pathlib
import subprocess

# -----------------------------------------------------------------------------
# Tools

def run_required(cmd):
    print(">>> {}".format(" ".join(cmd)))
    code = subprocess.call(cmd, shell=False)
    if code != 0:
        print("Error, command {} exited with {}".format(cmd, code))
        sys.exit(1)

def run_optional(cmd):
    print(">>> {}".format(" ".join(cmd)))
    return subprocess.call(cmd, shell=False)

# -----------------------------------------------------------------------------
# Main

def main():

    # Ask for target installation directory
    targetDir = input("Please enter installation directory")
    targetDir = os.path.abspath(targetDir)
    print("Target directory set: {}".format(targetDir))

    # Create target directory if not exists
    pathlib.Path(targetDir).mkdir(parents=True, exist_ok=True)

    # CD into it
    os.chdir(targetDir)

    # Run apt update
    run_required(["apt", "update"])

    # Install dependencies
    run_required(["apt-get", "-y", "install", "git", "doxygen", "zlib1g-dev", "cmake", "build-essential"])

    # Download pbrt-IILE
    # git clone --recursive https://github.com/giuliojiang/pbrt-v3-IISPT/
    run_required(["git", "clone", "--recursive", "https://github.com/giuliojiang/pbrt-v3-IISPT/"])

    # Download training dataset
    run_required(["wget", "-O", "dataset.tgz", "https://github.com/giuliojiang/pbrt-v3-IISPT-dataset/releases/download/v3/pbrt-v3-IISPT-dataset-indNewNormals-v02.tgz"])
    run_required(["tar", "-xf", "dataset.tgz"])
    os.remove("dataset.tgz")
    print("Downloaded training dataset")

    # Download neural network model
    run_required(["wget", "-O", "pbrt-v3-IISPT/iispt_model.tch", "https://github.com/giuliojiang/pbrt-v3-IISPT-dataset/releases/download/v4/iispt_model_10_2.tch"])
    print("Downloaded training model parameters")

    # Download and install Anaconda
    anacondaChoice = input("Would you like the installer to download and install Anaconda, Pytorch and Tensorboard? [y/n]")
    if anacondaChoice == "y":

        run_required(["wget", "-O", "anaconda.sh", "https://repo.anaconda.com/archive/Anaconda3-5.1.0-Linux-x86_64.sh"])
        run_required(["chmod", "+x", "anaconda.sh"])
        run_required([os.path.join(targetDir, "anaconda.sh")])
        os.remove("anaconda.sh")

        homeDir = os.path.expanduser("~")
        bashrcPath = os.path.join(homeDir, ".bashrc")
        tFilePath = os.path.join(targetDir, "t.sh")
        tFile = open(tFilePath, "w")
        tFile.write(". {}\n".format(bashrcPath))
        tFile.write("conda install pytorch torchvision -c pytorch\n")
        tFile.write("pip install tensorboardX tensorboard tensorflow\n")
        tFile.write("exit\n")
        tFile.close()
        subprocess.call('bash --init-file {}'.format(tFilePath), shell=True)
        
    # Download and install Node
    nodeChoice = input("Would you like the installer to download and install NodeJS? [y/n]")
    if nodeChoice == "y":

        run_required(["apt-get", "-y", "install", "curl"])
        subprocess.call("curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -", shell=True)
        run_required(["apt-get", "-y", "install", "nodejs"])

        # Install node modules
        os.chdir(os.path.join(targetDir, "pbrt-v3-IISPT", "bin"))
        run_required(["npm", "install"])

        os.chdir(os.path.join(targetDir, "pbrt-v3-IISPT", "tools"))
        run_required(["npm", "install"])

# -----------------------------------------------------------------------------
main()
