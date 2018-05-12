staticdir = __dirname;

var createPath = function(pname) {
    return url.format({
        pathname: pname,
        protocol: "file:",
        slashes: true
    });
};

