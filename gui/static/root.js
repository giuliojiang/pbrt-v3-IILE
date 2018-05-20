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
data.pbrtStatus = "Idle";
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

    priv.startPbrt();
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

priv.startPbrt = function() {
    log.info("Starting PBRT...");

    if (argv.length != 6) {
        alert("Expected 6 positional arguments. Got " + argv.length);
        return;
    }

    var pbrtExecPath = argv[2];
    var inputPath = argv[3];
    var indirectTasks = argv[4];
    var directTasks = argv[5];

    // CD into input pbrt file's directory
    var inputDir = path.dirname(inputPath);
    process.chdir(inputDir);

    data.pbrtProc = spawn("node", [pbrtExecPath, inputPath, "--iileIndirect=" + indirectTasks, "--iileDirect=" + directTasks, "--iileControl=" + data.controlDir], {
        detached: true
    });

    data.pbrtStatus = "Starting";

    data.pbrtProc.stdout.on("data", (data) => {
        log.info("STDOUT " + data);
    });

    data.pbrtProc.stderr.on("data", (data) => {
        log.info("STDERR " + data);
    });

    data.pbrtProc.on("close", function(code, signal) {
        data.pbrtStatus = "Exited ["+ code +"] ["+ signal +"]";
    });
};

// Call initialization ========================================================

performStartupActions();
