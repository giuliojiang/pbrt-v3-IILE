priv.tonemap = {}

// <exposure> a number to use manual exposure, or null to use autoexposure
priv.tonemap.tonemap = function(pfmPath, exposure, callback) {

    try {

        console.info("priv.tonemap.tonemap");

        // Copy file to a temporary one first
        var tPath = toControlFile("t.pfm");
        var tPngPath = toControlFile("t.png");
        fs.copyFileSync(pfmPath, tPath);

        var toolsDir = path.join(rootDir, "tools");
        var tonemapPy = path.join(toolsDir, "pfm_tonemap.py");

        var cmd = [];
        cmd.push(tonemapPy);
        cmd.push(tPath);
        if (exposure != null) {
            cmd.push(exposure.toString());
        }

        console.info("python3 " + cmd);

        var proc = spawn("python3", cmd);

        proc.stdout.on("data", (data) => {
            console.info("stdout " + data);
        });

        proc.stderr.on("data", (data) => {
            console.info("stderr " + data);
        });

        proc.on("close", function(code, signal) {
            var splt = pfmPath.split(".");
            var spltLen = splt.length;
            splt[spltLen - 1] = "png";
            var pngPath = splt.join(".");
            fs.copyFileSync(tPngPath, pngPath);
            console.info("priv.tonemap.tonemap complete ["+ code +"] ["+ signal +"]");
            callback();
        });

    } catch (err) {
        console.error(err);
        callback();
    }

};
