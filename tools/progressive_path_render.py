import os
import subprocess
import time

# =============================================================================
# Constants and settings

inputFiles = [
    "/home/gj/git/pbrt-v3-scenes/white-room/whiteRoomDaytimePath.pbrt",
    "/home/gj/git/pbrt-v3-scenes-extra/veach-ajar/scenePath.pbrt",
    "/home/gj/git/pbrt-v3-custom-scenes/mbed1/scenePath.pbrt"
]

outputDir = "/home/gj/git/pbrt-v3-IISPT/tmp"

maxSpp = 2048

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

def processFileAtQuality(fpath, spp):
    # Set environment variable
    os.environ["IILE_PATH_SAMPLES_OVERRIDE"] = "{}".format(spp)

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
    runProcess(cmd)

    # End timer
    timeEnd = time.time()
    secondsElapsed = timeEnd - timeStart
    secondsElapsed = int(secondsElapsed)

    # Record on file
    statFile = open(statFilePath, "w")
    statFile.write("{}\n".format(secondsElapsed))
    statFile.close()

def processFile(fpath):
    spp = 1
    while spp <= maxSpp:
        processFileAtQuality(fpath, spp)
        spp *= 2

def main():
    for fp in inputFiles:
        processFile(fp)

# =============================================================================
# Main

main()