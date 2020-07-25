#!/usr/bin/env python3

import os
import subprocess
import shutil
import sys

# Directory detection =========================================================

rootDir = os.path.abspath(os.path.dirname(__file__))


# Utilities ===================================================================

def run(cmd):
    print(">>> {}".format(" ".join(cmd)))
    code = subprocess.call(cmd, shell=False)
    if code != 0:
        print("Failed.")
        sys.exit(1)

# Main script =================================================================

def main():

    os.chdir(rootDir)

    # Main build --------------------------------------------------------------

    run([
        "rm",
        "-rf",
        "build"
    ])

    run([
        "mkdir",
        "build"
    ])

    buildDir = os.path.join(rootDir, "build")

    os.chdir(buildDir)

    # Cmake

    run([
        "cmake",
        ".."
    ])

    # Make

    run([
        "make",
        "-j16"
    ])

    # npm install -------------------------------------------------------------
    npmDirs = ["bin", "gui", "tools"]
    for npmDir in npmDirs:
        fullDir = os.path.join(rootDir, npmDir)
        os.chdir(fullDir)
        run(["npm", "install"])

    # cpfm build --------------------------------------------------------------
    cpfmDir = os.path.join(rootDir, "tools", "cpfm")
    cpfmBuildDir = os.path.join(cpfmDir, "build")
    if os.path.exists(cpfmBuildDir):
        shutil.rmtree(cpfmBuildDir)
    os.mkdir(cpfmBuildDir)
    os.chdir(cpfmBuildDir)

    run([
        "cmake",
        "../cpfm"
    ])

    run([
        "make",
        "-j4"
    ])

# Run =========================================================================

main()
