import os
import sys
import shutil
import subprocess

toolsDir = os.path.abspath(os.path.dirname(__file__))
rootDir = os.path.dirname(toolsDir)

argv = sys.argv[1:]

try:
    nodejsDownloadLink = argv[0]
    destDir = os.path.abspath(argv[1])
    exporterDir = os.path.abspath(argv[2])
except:
    print("Requires arguments: <nodejs download link> <destination directory> <exporter directory>")
    sys.exit(1)

# Check if destination directory exists
if os.path.exists(destDir):
    print("Destination directory exists.")
    sys.exit(1)

# Make the destination directory
os.mkdir(destDir)

# Make the subdirectories for the different package versions
pIileDir = os.path.join(destDir, "PBRT-IILE")
pFull = os.path.join(destDir, "FULLPACKAGE")
pExp = os.path.join(destDir, "EXPORTERONLY")
os.mkdir(pIileDir)
os.mkdir(pFull)
os.mkdir(pExp)

# Create IILE only package ====================================================

'''
PBRT-IILE
    pbrt     launcher
    node
        bin
            node
            npm
            ...
    iile
        bin
            pbrt
        build
        ml
        ...
'''

def packageIILE(iileDir):
    os.mkdir(iileDir)

    buildDir = os.path.join(iileDir, "build")
    os.mkdir(buildDir)

    # Copy objects specified
    listPath = os.path.join(toolsDir, "packageList.txt")
    listFile = open(listPath, "r")
    for line in listFile:
        line = line.strip()
        if line == "":
            continue
        
        sourcePath = os.path.join(rootDir, line)
        destPath = os.path.join(iileDir, line)

        print("Copying {} to {}".format(sourcePath, destPath))

        if os.path.isdir(sourcePath):
            shutil.copytree(sourcePath, destPath)
        else:
            shutil.copy(sourcePath, destPath)

packageIILE(os.path.join(pIileDir, "iile"))

def installNode(destDir):
    nodeArchivePath = "/tmp/node.tar.xz"
    subprocess.call(["wget", "-O", nodeArchivePath, nodejsDownloadLink])
    parentDir = os.path.dirname(destDir)
    destBasename = os.path.basename(destDir)
    os.chdir(parentDir)
    subprocess.call(["tar", "-vxf", nodeArchivePath])
    content = os.listdir(parentDir)
    for c in content:
        if c.startswith("node"):
            subprocess.call(["mv", c, destBasename])

installNode(os.path.join(pIileDir, "node"))

# Create launcher link
shutil.copy(
    os.path.join(toolsDir, "resources", "pbrt"),
    os.path.join(pIileDir, "pbrt")
)
