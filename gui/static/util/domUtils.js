var domUtils = {};

// <targetId> the DOM id of the <img> element
domUtils.loadImage = function(targetId, imagePath) {

    var elem = document.getElementById(targetId);

    // Check if imagePath exists
    if (!fs.existsSync(imagePath)) {
        elem.src = "";
    } else {
        elem.src = urlUtils.pathToUrl(imagePath);
    }

}

domUtils.resizeImage = function(targetId, ratio) {
    var elem = document.getElementById(targetId);

    elem.style.width = "auto";
    elem.style.height = "auto";

    var realWidth = elem.width;

    var scaledWidth = ratio * realWidth;

    elem.style.width = scaledWidth;
}
