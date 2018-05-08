#ifndef IISPT_H
#define IISPT_H

#include <iostream>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/wait.h>
#include <chrono>
#include <thread>

#include "tools/childprocess.hpp"
#include "integrators/iisptschedulemonitor.h"
#include "integrators/iisptfilmmonitor.h"
#include "tools/iisptrng.h"
#include "integrators/iisptnnconnector.h"

using namespace pbrt;

// Test the new iispt schedule monitor
void test_main8()
{
    std::cerr << "test_main8()\n";

    std::unique_ptr<IisptScheduleMonitor> schedule_monitor (
                new IisptScheduleMonitor(
                    Bounds2i(
                        Point2i(10, 10),
                        Point2i(1280, 720)
                        )
                    )
                );

    for (int i = 0; i < 250; i++) {
        IisptScheduleMonitorTask task =
                schedule_monitor->next_task();
        std::cerr << "Start ["<< task.x0 <<"]["<< task.y0 <<
                     "] Finish ["<< task.x1 <<"]["<< task.y1 <<
                     "] Radius ["<< task.tilesize <<"]\n";
    }
}

// Test importance sampling and CDFs
void test_main7()
{
    std::cerr << "test_main7()\n";

    std::unique_ptr<IntensityFilm> intensity (
                new IntensityFilm(
                    32, 32
                    )
                );

    for (int y = 0; y < 32; y++) {
        for (int x = 0; x < 32; x++) {
            intensity->set(x, y, 0.2, 0.2, 0.2);
        }
    }

    // Set higher intensity in corner [0, 0] - [5, 5]
    for (int y = 0; y <= 5; y++) {
        for (int x = 0; x <= 5; x++) {
            intensity->set(x, y, 10.0, 10.0, 10.0);
        }
    }

    intensity->compute_cdfs();

    std::unique_ptr<IisptRng> rng (
                new IisptRng(0)
                );

    for (int i = 0; i < 1000; i++) {
        float rx = rng->uniform_float();
        float ry = rng->uniform_float();
        std::cerr << "Randoms ["<< rx <<"] ["<< ry <<"]\n";
        int cx;
        int cy;
        float prob;
        PfmItem item = intensity->importance_sample_camera_coord(
                    rx,
                    ry,
                    &cx,
                    &cy,
                    &prob
                    );
        std::cerr << "Sampled ["<< item.magnitude() <<"] at ["<< cx <<"]-["<< cy <<"] with prob ["<< prob <<"]\n";
    }
}

void test_main5()
{
    std::cerr << "Running test main 5\n";

    std::unique_ptr<IisptRng> rng (
                new IisptRng(0)
                );

    for (int i = 0; i < 25; i++) {
        float f = rng->uniform_float();
        // std::cerr << f << std::endl;

        bool b = rng->bool_probability(0.9);
        std::cerr << b << std::endl;
    }
}

void test_main2() {
    std::cerr << "Running test main 2" << std::endl;

    char *const argv[] = {"python3", "-u", "/home/gj/git/pbrt-v3-IISPT/tools/test_python_child_bin.py", NULL};
    ChildProcess cp (std::string("python3"), argv);
    cp.write_float32(595.0);
    Float fresult;
    int status = cp.read_float32(&fresult);
    if (status) {
        std::cerr << "Error when reading the float" << std::endl;
    } else {
        std::cerr << "Got a float: " << fresult << std::endl;
    }

    status = cp.read_float32(&fresult);
    if (status) {
        std::cerr << "Reading got nothing" << std::endl;
    }

    exit(0);
}

void test_main1() {
    std::cerr << "Running test main 1" << std::endl;

    char *const argv[] = {"python3", "-u", "/home/gj/git/pbrt-v3-IISPT/tools/test_python_child.py", NULL};
    ChildProcess cp (std::string("python3"), argv);
    cp.write_char('b');
    cp.write_char('\n');
    while (1) {
        char r = cp.read_char();
        if (r == '\0') {
            exit(0);
        }
        std::cerr << "["<< r <<"]" << std::endl;
    }
}

void test_main0() {
    std::cerr << "Running test main" << std::endl;

    pid_t pid;
    int stdout_pipe[2];
    int stdin_pipe[2];

    pipe(stdout_pipe);
    pipe(stdin_pipe);
    pid = fork();

    if (pid == -1) {
        std::cerr << "fork() failed" << std::endl;
        exit(1);
    } if (pid==0) {
        // Child process

        dup2(stdout_pipe[1], STDOUT_FILENO); // Subprocess receives write end of stdout pipe
        dup2(stdin_pipe[0], STDIN_FILENO); // Subprocess receives read end of stdin pipe
        close(stdout_pipe[0]);
        close(stdout_pipe[1]);
        close(stdin_pipe[0]);
        close(stdin_pipe[1]);

        execlp("python3", "python3", "-u", "/home/gj/git/pbrt-v3-IISPT/tools/test_python_child.py", NULL); // Should never return in case of success

        std::cerr << "Failed execlp()" << std::endl;

        exit(1);
    }

    // Original process
    std::cerr << "This is the original process" << std::endl;

    int buffsize = 100;
    char buffer[buffsize];
    write(stdin_pipe[1], "b\n", 2);
    while (1) {
        std::cerr << "Reading..." << std::endl;
        ssize_t count = read(stdout_pipe[0], buffer, sizeof(buffer)); // Read from stdout's read end
        std::cerr << "Read count is " << count << std::endl;
        if (count <= 0) {
            std::cerr << "EOF" << std::endl;
            break;
        } else {
            std::cerr << "From child: [" << buffer << "]" << std::endl;
        }

        std::this_thread::sleep_for(std::chrono::seconds(1));
        std::cerr << "Parent: writing a" << std::endl;
        write(stdin_pipe[1], "a\n", 2);
    }

    exit(0);
}

#endif // IISPT_H
