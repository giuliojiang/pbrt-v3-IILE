staticdir = __dirname;

var url = require("url");
var randomstring = require("randomstring");
var remote = require("electron").remote;
var fs = require("fs");
var fsExtra = require("fs-extra");
var path = require("path");
const { spawn } = require('child_process');

var argv = remote.getGlobal("argv").argv;

var data = {};
data.controlDir = "";
data.exposure = 0;
data.pbrtStatus = "Idle";
data.pbrtProc = null;

var priv = {};

var touchFile = function(fpath) {
    fs.closeSync(fs.openSync(fpath, 'w'));
};

var toControlFile = function(controlString) {
    return path.join(data.controlDir, controlString);
};

var controlWriteExposure = function() {
    // Clear existing exposure controls
    var dircontent = fs.readdirSync(data.controlDir);
    for (var i = 0; i < dircontent.length; i++) {
        if (dircontent[i].startsWith("control_gain_")) {
            var fullPath = path.join(data.controlDir, dircontent[i]);
            fsExtra.removeSync(fullPath);
            console.info("Removing: " + dircontent[i]);
        }
    }

    var exposureString = "control_gain_" + data.exposure;
    touchFile(toControlFile(exposureString));
};

var performStartupActions = function() {
    data.controlDir = path.join("/tmp", randomstring.generate(20));

    console.info("Control directory: " + data.controlDir);

    // Create control directory
    fs.mkdirSync(data.controlDir);

    // Write exposure
    controlWriteExposure();

    console.info("argv");
    console.info(argv);

    priv.startPbrt();
}

var bodyUnload = function() {
    if (data.pbrtProc) {
        data.pbrtProc.kill();
    }

    fsExtra.removeSync(data.controlDir);
};

priv.startPbrt = function() {
    console.info("Starting PBRT...");

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

    data.pbrtProc = spawn("node", [pbrtExecPath, inputPath, "--iileIndirect=" + indirectTasks, "--iileDirect=" + directTasks, "--iileControl=" + data.controlDir]);

    data.pbrtStatus = "Starting";

    data.pbrtProc.stdout.on("data", (data) => {
        console.info("STDOUT " + data);
    });

    data.pbrtProc.stderr.on("data", (data) => {
        console.info("STDOUT " + data);
    });

    data.pbrtProc.on("close", function(code, signal) {
        data.pbrtStatus = "Exited ["+ code +"] ["+ signal +"]";
    });
};

// Call initialization ========================================================

performStartupActions();
