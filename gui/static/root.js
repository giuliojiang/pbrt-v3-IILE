staticdir = __dirname;

var url = require("url");

var pathToUrl = function(pname) {
    return url.format({
        pathname: pname,
        protocol: "file:",
        slashes: true
    });
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
