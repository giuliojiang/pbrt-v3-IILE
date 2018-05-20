var urlUtils = {};

urlUtils.pathToUrl = function(pname) {
    return url.format({
        pathname: pname,
        protocol: "file:",
        slashes: true
    }) + "?" + new Date().getTime();
};
