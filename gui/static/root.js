staticdir = __dirname;

var url = require("url");
var randomstring = require("randomstring");
var remote = require("electron").remote;

var argv = remote.getGlobal("argv").argv;

var theRandomString = randomstring.generate(20);

console.info("A random string: " + theRandomString);

console.info("argv");
console.info(argv);

var bodyUnload = function() {
    alert("unloading!");
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
