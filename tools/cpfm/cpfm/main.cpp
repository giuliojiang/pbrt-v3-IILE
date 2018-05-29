#include <iostream>
#include <vector>
#include "utils.h"
#include "filereader.h"
#include "image.h"
#include "lodepng.h"

int main(int argc, char** argv)
{
    std::string inputFilePath;
    bool autoExposure = true;
    float exposure;

    for (int i = 1; i < argc; i++) {
        if (i == 1) {
            inputFilePath = std::string(argv[i]);
        }
        if (i == 2) {
            autoExposure = false;
            try {
                exposure = std::stof(std::string(argv[i]));
            } catch (const std::invalid_argument& ia) {
                std::cerr << "Could not parse exposure value" << std::endl;
                terminate();
            }
        }
    }

    if (inputFilePath.empty()) {
        std::cerr << "Usage: ./cpfm <input.pfm> [exposure]" << std::endl;
        terminate();
    }

    if (!hasEnding(inputFilePath, ".pfm")) {
        std::cerr << "Input file must be a .pfm\n";
        terminate();
    }

    std::string outputFilePath;
    {
        int len = inputFilePath.size();
        int end = len - 4;
        outputFilePath = inputFilePath.substr(0, end) + std::string(".png");
    }
    std::cerr << "Output filename will be " << outputFilePath << std::endl;

    FileReader reader (inputFilePath);

    // Magic line
    std::string line = reader.readLine();
    if (line == std::string("Pf")) {
        std::cerr << "Single-channel PFM is not supported\n";
        terminate();
    }
    if (line != std::string("PF")) {
        std::cerr << "Unrecognized file format\n";
        terminate();
    }

    // Dimensions
    line = reader.readLine();
    int width;
    int height;
    {
        std::vector<std::string> splt = split(line, ' ');
        if (splt.size() != 2) {
            std::cerr << "Could not read width and height properties\n";
            terminate();
        } else {
            try {
                width = std::stoi(splt[0]);
                height = std::stoi(splt[1]);
            } catch (const std::invalid_argument& ia) {
                std::cerr << "Error parsing width and height information\n";
                terminate();
            }
        }
    }
    std::cerr << "Width ["<< width <<"] Height ["<< height <<"]\n";

    // Endianness and others. Ignore.
    line = reader.readLine();
    std::cerr << "Read line ["<< line <<"]\n";

    // Compute total number of bytes
    int totalFloats = width * height * 3;
    int totalBytes = totalFloats * 4;
    std::vector<float> floatBuff (totalFloats);

    // Read all data
    reader.read(&floatBuff[0], totalBytes);
    reader.close();

    std::vector<unsigned char> tonemapped;
    if (autoExposure) {
        tonemapAuto(floatBuff, tonemapped);
    } else {
        tonemap(floatBuff, exposure, tonemapped);
    }
    flip(tonemapped, width, height);

    // Output to PNG
    lodepng::encode(
                outputFilePath,
                &tonemapped[0],
                width,
                height,
                LodePNGColorType::LCT_RGB
                );

}
