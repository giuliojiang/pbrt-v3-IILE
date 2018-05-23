staticdir = __dirname;
var path = require("path");
guiDir = path.dirname(staticdir);
rootDir = path.dirname(guiDir);

var url = require("url");
var randomstring = require("randomstring");
var remote = require("electron").remote;
var fs = require("fs");
var fsExtra = require("fs-extra");
const { spawn } = require('child_process');

var shd = remote.getGlobal("shd");
var argv = shd.argv;
var log = shd.console;

var data = {};
data.controlDir = "";
data.pbrtProc = null;

var priv = {};

var touchFile = function(fpath) {
    fs.closeSync(fs.openSync(fpath, 'w'));
};

var toControlFile = function(controlString) {
    return path.join(data.controlDir, controlString);
};

var performStartupActions = function() {
    data.controlDir = path.join("/tmp", randomstring.generate(20));

    log.info("Control directory: " + data.controlDir);

    // Create control directory
    fs.mkdirSync(data.controlDir);

    log.info("argv");
    log.info(argv);
}

window.onbeforeunload = (e) => {
    log.info("Window close event");

    // Unlike usual browsers that a message box will be prompted to users, returning
    // a non-void value will silently cancel the close.
    // It is recommended to use the dialog API to let the user confirm closing the
    // application.
    e.returnValue = false // equivalent to `return false` but not recommended

    if (data.pbrtProc) {
        data.pbrtProc.kill("SIGINT");
        log.info("Sent SIGINT to PBRT");
    }

    shd.win.hide();

    setTimeout(function() {
        log.info("Ready to close...");
        fsExtra.removeSync(data.controlDir);
        shd.win.destroy();
    }, 1000);
}

// <onPbrtExit> a callback(code, signal) when the subprocess PBRT
// exits
//
// <onRenderFinish> callback() called when rendering completes
//
// <onIndirectProgress> function(p) p is a Float
//
// <onDirectProgress> function(p) p is a Float
priv.startPbrt = function(onPbrtExit, onRenderFinish, onIndirectProgress, onDirectProgress) {
    log.info("Starting PBRT...");

    if (argv.length != 6) {
        alert("Expected 6 positional arguments. Got " + argv.length);
        return;
    }

    var pbrtExecPath = argv[2];
    var inputPath = argv[3];
    var indirectTasks = argv[4];
    var directTasks = argv[5];

    var parseLine = function(line) {
        if (line.startsWith("#")) {
            var splt = line.split("!");
            if (splt.length != 2) {
                return;
            }

            var key = splt[0];
            var value = splt[1];

            if (key == "#DIRECTPROGRESS") {
                var ratio = parseFloat(value);
                onDirectProgress(ratio);
            } else if (key == "#INDPROGRESS") {
                var ratio = parseFloat(value);
                onIndirectProgress(ratio);
            } else if (key == "#FINISH") {
                onRenderFinish();
            }
        }
    }

    // CD into input pbrt file's directory
    var inputDir = path.dirname(inputPath);
    process.chdir(inputDir);
    
    log.info("PATH is " + process.env.PATH);

    data.pbrtProc = spawn("node", [pbrtExecPath, inputPath, "--iileIndirect=" + indirectTasks, "--iileDirect=" + directTasks, "--iileControl=" + data.controlDir], {
        detached: true
    });
    
    data.pbrtProc.on("error", function(error) {
        alert("PBRT error: " + error);
    });

    data.pbrtProc.stdout.on("line", (line) => {
        log.info("LINE " + line);
        parseLine(line);
    });

    emitLines(data.pbrtProc.stdout);

    data.pbrtProc.stderr.on("data", (data) => {
        log.info("STDERR " + data);
    });

    data.pbrtProc.on("close", function(code, signal) {
        log.info("Exited ["+ code +"] ["+ signal +"]");
        onPbrtExit(code, signal);
    });
};
