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
pExp = os.path.join(destDir, "render_pbrt")
os.mkdir(pIileDir)

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

def copyIILEContent(iileDir):
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

def installNode(destDir):
    nodeArchivePath = "/tmp/node.tar.xz"
    subprocess.call(["wget", "-O", nodeArchivePath, nodejsDownloadLink])
    parentDir = os.path.dirname(destDir)
    destBasename = os.path.basename(destDir)
    os.chdir(parentDir)
    subprocess.call(["tar", "-xf", nodeArchivePath])
    content = os.listdir(parentDir)
    for c in content:
        if c.startswith("node"):
            subprocess.call(["mv", c, destBasename])

def packageIILE(pIileDir):
        
    copyIILEContent(os.path.join(pIileDir, "iile"))

    installNode(os.path.join(pIileDir, "node"))

    # Create launcher link
    shutil.copy(
        os.path.join(toolsDir, "resources", "pbrt"),
        os.path.join(pIileDir, "pbrt")
    )

packageIILE(pIileDir)

# Tar it
print("Compressing PBRT-IILE")
os.chdir(destDir)
subprocess.call([
    "tar",
    "-I",
    "pigz",
    "-cf",
    "PBRT-IILE.tgz",
    "PBRT-IILE"
])

# Create Blender exporter only package ========================================

shutil.copytree(
    os.path.join(exporterDir, "render_pbrt"),
    os.path.join(pExp)
)

print("Compressing Exporter")
os.chdir(destDir)

subprocess.call([
    "zip",
    "-r",
    "pbrtExporter.zip",
    "render_pbrt"
])

# Create Blender exporter with IILE included ==================================

shutil.copy(
    os.path.join(destDir, "PBRT-IILE.tgz"),
    os.path.join(pExp, "PBRT-IILE.tgz")
)

print("Compressing PBRT-IILE + Exporter")
os.chdir(destDir)
subprocess.call([
    "zip",
    "-r",
    "pbrtExporterWithIile.zip",
    "render_pbrt"
])

# Cleanup

shutil.rmtree(pIileDir)
shutil.rmtree(pExp)