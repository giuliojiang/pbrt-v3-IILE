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
