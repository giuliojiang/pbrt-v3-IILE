staticdir = __dirname;

var url = require("url");
var randomstring = require("randomstring");
var remote = require("electron").remote;
var fs = require("fs");
var fsExtra = require("fs-extra");
var path = require("path");

var argv = remote.getGlobal("argv").argv;

var data = {};
data.controlDir = "";
data.exposure = 20;

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
}

var bodyUnload = function() {
    fsExtra.removeSync(data.controlDir);
};

var pathToUrl = function(pname) {
    return url.format({
        pathname: pname,
        protocol: "file:",
        slashes: true
    }) + "?" + new Date().getTime();
};

var loadImage = function(targetId, imagePath) {

    var elem = document.getElementById(targetId);
    // Remove all children of the target element
    while (elem.firstChild) {
        elem.removeChild(elem.firstChild);
    }

    // Check if imagePath exists
    if (!fs.existsSync(imagePath)) {
        // Display unavailable text
        var txt = document.createElement("p");
        txt.innerHTML = "unavailable";
        elem.appendChild(txt);
        return;
    } else {
        // Create new IMG node
        var img = document.createElement("img");
        img.src = pathToUrl(imagePath);
        // Add the node
        elem.appendChild(img);
    }
};

// Call initialization ========================================================

performStartupActions();
