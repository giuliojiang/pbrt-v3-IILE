#!/usr/bin/env python3

import os
import subprocess

# Directory detection =========================================================

rootDir = os.path.abspath(os.path.dirname(__file__))


# Utilities ===================================================================

def run(cmd):
    print(">>> {}".format(" ".join(cmd)))
    subprocess.call(cmd, shell=False)

# Main script =================================================================

def main():

    os.chdir(rootDir)

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
        "-j4"
    ])

# Run =========================================================================

main()