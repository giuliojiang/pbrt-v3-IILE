import os
import subprocess

# =============================================================================
# Constants and settings

inputFiles = [
    "/home/gj/git/pbrt-v3-scenes/white-room/whiteRoomDaytimePath.pbrt",
    "/home/gj/git/pbrt-v3-scenes-extra/bedroom/scenePath.pbrt",
    "/home/gj/git/pbrt-v3-scenes-extra/veach-ajar/scenePath.pbrt"
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

    # Change working directory
    os.chdir(fdir)

    # Start process
    cmd = []
    cmd.append(pbrtPath)
    cmd.append(fpath)
    cmd.append(outFilePath)
    runProcess(cmd)

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