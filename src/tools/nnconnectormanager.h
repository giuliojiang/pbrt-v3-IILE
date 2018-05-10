#ifndef NNCONNECTORMANAGER_H
#define NNCONNECTORMANAGER_H

#include <iostream>
#include <csignal>
#include <vector>
#include <memory>
#include "integrators/iisptnnconnector.h"

namespace pbrt {
namespace iile {

class NnConnectorManager
{
private:
    std::vector<std::shared_ptr<IisptNnConnector>> nnConnectors;

    NnConnectorManager()
    {

    }

public:
    static NnConnectorManager& getInstance()
    {
        static NnConnectorManager instance;
        return instance;
    }

    NnConnectorManager(NnConnectorManager const&) = delete;
    void operator=(NnConnectorManager const&)     = delete;

    void start(int noThreads);

    std::shared_ptr<IisptNnConnector> get(int threadNumber);

    void stopAll();
};



}
}

#endif // NNCONNECTORMANAGER_H
