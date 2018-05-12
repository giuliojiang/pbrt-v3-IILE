staticdir = __dirname;

var url = require("url");
var randomstring = require("randomstring");
var remote = require("electron").remote;
var fs = require("fs");
var fsExtra = require("fs-extra");

var argv = remote.getGlobal("argv").argv;

controlDir = "/tmp/" + randomstring.generate(20);

console.info("Control directory: " + controlDir);

// Create control directory
fs.mkdirSync(controlDir);

console.info("argv");
console.info(argv);

var bodyUnload = function() {
    fsExtra.removeSync(controlDir);
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
    // Create new IMG node
    var img = document.createElement("img");
    img.src = pathToUrl(imagePath);
    // Add the node
    elem.appendChild(img);
};
