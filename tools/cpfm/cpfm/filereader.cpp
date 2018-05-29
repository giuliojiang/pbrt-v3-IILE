#include "filereader.h"

FileReader::FileReader(std::string filePath)
{
    this->file.open(filePath, std::ios::in | std::ios::binary);
    if (!file.is_open()) {
        std::cerr << "Could not open file\n";
        terminate();
    }
}

std::string FileReader::readLine()
{
    std::string buff;
    std::getline(file, buff, '\n');
    return buff;
}

void FileReader::read(void* buff, int noBytes)
{
    file.read((char*)buff, noBytes);
    int bytesRead = file.gcount();
    if (noBytes != bytesRead) {
        std::cerr << "Could not read ["<< noBytes <<"] bytes, only read ["<< bytesRead <<"]\n";
        terminate();
    }
}
