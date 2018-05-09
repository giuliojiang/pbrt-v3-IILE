#include "nnconnectormanager.h"

namespace pbrt {
namespace iile {

void NnConnectorManager::start(int noThreads)
{
    if (nnConnectors.size() > 0) {
        std::cerr << "nnconnectormanager.cpp: called start() but there are already nnConnectors in the vector\n";
        std::raise(SIGKILL);
    }

    for (int i = 0; i < noThreads; i++) {
        std::cerr << "nnconnectormanager.cpp: Starting NN connector " << i << std::endl;
        nnConnectors.push_back(
                    std::shared_ptr<IisptNnConnector>(
                        new IisptNnConnector()
                        )
                    );
    }
}

std::shared_ptr<IisptNnConnector> NnConnectorManager::get(int threadNumber)
{
    if (threadNumber >= nnConnectors.size()) {
        std::cerr << "nnconnectormanager.cpp: Requested connector number ["<< threadNumber <<"] but only ["<< nnConnectors.size() <<"] available\n";
        std::raise(SIGKILL);
    }

    return nnConnectors[threadNumber];
}

}


}
