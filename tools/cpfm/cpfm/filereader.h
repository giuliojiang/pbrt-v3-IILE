#ifndef FILEREADER_H
#define FILEREADER_H

#include <iostream>
#include <fstream>

#include "utils.h"

class FileReader
{
private:

    std::ifstream file;

public:

    FileReader(std::string filePath);

    std::string readLine();

    void read(void* buff, int noBytes);

    void close();

};

#endif // FILEREADER_H
