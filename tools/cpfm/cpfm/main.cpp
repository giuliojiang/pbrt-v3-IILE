#include <iostream>
#include "utils.h"
#include "filereader.h"

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

    FileReader reader (inputFilePath);

    std::string line = reader.readLine();
    std::cerr << "Read line ["<< line <<"]\n";

    line = reader.readLine();
    std::cerr << "Read line ["<< line <<"]\n";

    line = reader.readLine();
    std::cerr << "Read line ["<< line <<"]\n";

    float buff[10];
    reader.read(buff, 10 * 4);
    for (int i = 0; i < 10; i++) {
        std::cerr << buff[i] << std::endl;
    }

}
