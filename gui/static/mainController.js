var mainApp = angular.module("mainApp", []);

mainApp.controller("main_controller", function($scope) {

    $scope.title = "pbrt v3 IILE";

    $scope.d = {};

    // Preview images =========================================================

    $scope.d.activePreview = "out_combined";

    $scope.buttonCombined = function() {
        $scope.d.activePreview = "out_combined";
        $scope.reloadImage();
    };

    $scope.buttonIndirect = function() {
        $scope.d.activePreview = "out_indirect";
        $scope.reloadImage();
    };

    $scope.buttonDirect = function() {
        $scope.d.activePreview = "out_direct";
        $scope.reloadImage();
    };

    $scope.reload = {};

    $scope.reloadImage = function(callback) {

        console.info("Reloading image...");

        var activePreview = $scope.d.activePreview;

        // Execute tonemapping job
        priv.tonemap.tonemap(
            toControlFile(activePreview + ".pfm"),
            $scope.exposure.auto ? null : $scope.exposure.value,
            function() {

                // Reload preview image
                domUtils.loadImage("img_main", toControlFile(activePreview + ".bmp"));
                domUtils.resizeImage("img_main", $scope.zoom.scale);

                if (callback) {
                    callback();
                }
                return;

            }
        );

    };

    // Exposure controls ======================================================

    $scope.exposure = {};
    $scope.exposure.auto = true;
    $scope.exposure.value = 0;

    $scope.buttonExposureApply = function() {
        console.info("Updating exposure control");
        $scope.exposure.auto = false;
        $scope.reloadImage();
    };

    $scope.buttonAutoexpose = function() {
        console.info("Enable autoexposure");
        $scope.exposure.auto = true;
        $scope.reloadImage();
    };

    $scope.buttonSaveAs = function() {
        console.info("Save as...");
        var savePath = remote.dialog.showSaveDialog({
            title: "Save Image As BMP",
            filters: [
                {
                    name: "BMP Image",
                    extensions: [".bmp"]
                }
            ]
        });
        console.info("Savepath is " + savePath);
        fs.copyFileSync(
            toControlFile($scope.d.activePreview + ".bmp"),
            savePath
        );
    };

    // ========================================================================
    // Progress

    $scope.progress = {};
    $scope.progress.finish = false;
    $scope.progress.dir = 0;
    $scope.progress.ind = 0;
    $scope.d.timeElapsedText = "";

    // ========================================================================
    // Styles

    $scope.styles = {};

    $scope.styles.progressBar = function() {
        if ($scope.progress.finish) {
            return "j_cl_greenbg";
        } else {
            return "";
        }
    }

    // ========================================================================
    // Zoom

    $scope.zoom = {};
    $scope.zoom.scale = 1.0;

    $scope.zoom.buttonMinus = function() {
        $scope.zoom.scale *= 0.85;
        if ($scope.zoom.scale < 0.05) {
            $scope.zoom.scale = 0.05;
        }
        domUtils.resizeImage("img_main", $scope.zoom.scale);
    };

    $scope.zoom.buttonPlus = function() {
        $scope.zoom.scale *= 1.2;
        domUtils.resizeImage("img_main", $scope.zoom.scale);
    };

    $scope.zoom.button100 = function() {
        $scope.zoom.scale = 1.0;
        domUtils.resizeImage("img_main", $scope.zoom.scale);
    };

    $scope.zoom.getPercentage = function() {
        return (100 * $scope.zoom.scale).toFixed(2);
    };

    // ========================================================================
    // Startup

    $scope.startupFunc = function() {
        performStartupActions();
        priv.startPbrt(
            // onPbrtExit
            function(code, signal, elapsed) {
                var secondsElapsed = elapsed / 1000;
                $scope.d.timeElapsedText = "Completed in ["+ secondsElapsed +"] seconds";
                $scope.$apply();
            },
            // onRenderFinish
            function() {
                $scope.progress.finish = true;
                $scope.progress.ind = 100;
                $scope.progress.dir = 100;
                $scope.reloadImage();
                $scope.$apply();
            },
            // onIndirectProgress
            function(progress) {
                var newVal = 100 * progress;
                if (newVal > $scope.progress.ind) {
                    $scope.progress.ind = newVal;
                }
                $scope.$apply();
            },
            // onDirectProgress
            function(progress) {
                var newVal = 100 * progress;
                if (newVal > $scope.progress.dir) {
                    $scope.progress.dir = newVal;
                }
                $scope.$apply();
            },
            // onRefresh
            function() {
                $scope.reloadImage();
            }
        );
    };

    $scope.startupFunc();

});
