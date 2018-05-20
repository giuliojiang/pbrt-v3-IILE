import os
import subprocess
import time

# =============================================================================
# Constants and settings

# Each has:
# - filepath
# - directSpp
inputFiles = [
    # ["/home/gj/git/pbrt-v3-scenes/white-room/whiteroom-daytime.pbrt", 16],
    ["/home/gj/git/pbrt-v3-scenes-extra/veach-ajar/scene.pbrt", 2],
    # ["/home/gj/git/pbrt-v3-custom-scenes/mbed1/scene.pbrt", 64]
]

outputDir = "/home/gj/git/pbrt-v3-IISPT/tmpiile"

maxSpp = 256

# =============================================================================
# Directories configuration

toolsDir = os.path.abspath(os.path.dirname(__file__))
rootDir = os.path.dirname(toolsDir)
binDir = os.path.join(rootDir, "bin")
pbrtPath = os.path.join(binDir, "pbrt")

# =============================================================================
# Function definitions

def runProcess(cmd):
    print(">>> {}".format(cmd))
    subprocess.call(cmd, shell=False)

def processFileAtQuality(fdata, spp):

    fpath, directSpp = fdata

    # Generate output file name
    fdir = os.path.dirname(fpath)
    sceneName = os.path.basename(fdir)
    outFileName = "{}_{}.pfm".format(sceneName, spp)
    outFilePath = os.path.join(outputDir, outFileName)
    statFileName = "{}_{}.txt".format(sceneName, spp)
    statFilePath = os.path.join(outputDir, statFileName)

    # Skip if already processed
    if os.path.exists(statFilePath):
        return

    # Change working directory
    os.chdir(fdir)

    # Start timer
    timeStart = time.time()

    # Start process
    cmd = []
    cmd.append(pbrtPath)
    cmd.append(fpath)
    cmd.append(outFilePath)
    cmd.append("--iileIndirect={}".format(spp))
    cmd.append("--iileDirect={}".format(directSpp))
    runProcess(cmd)

    # End timer
    timeEnd = time.time()
    secondsElapsed = timeEnd - timeStart
    secondsElapsed = int(secondsElapsed)

    # Record on file
    statFile = open(statFilePath, "w")
    statFile.write("{}\n".format(secondsElapsed))
    statFile.close()

def processFile(fdata):
    spp = 0
    while spp <= maxSpp:
        processFileAtQuality(fdata, spp)
        if spp == 0:
            spp = 1
        else:
            spp *= 2

def main():
    for fdata in inputFiles:
        processFile(fdata)

# =============================================================================
# Main

main()