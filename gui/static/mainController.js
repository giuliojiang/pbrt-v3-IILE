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
    $scope.reload.wip = false;

    $scope.reloadImage = function(callback) {

        // Only allow 1 to execute at a time
        if ($scope.reload.wip) {
            if (callback) {
                callback();
            }
            return;
        }

        $scope.reload.wip = true;

        console.info("Reloading image...");

        var activePreview = $scope.d.activePreview;

        // Execute tonemapping job
        priv.tonemap.tonemap(
            toControlFile(activePreview + ".pfm"),
            $scope.exposure.auto ? null : $scope.exposure.value,
            function() {

                // Reload preview image
                domUtils.loadImage("img_main", toControlFile(activePreview + ".png"));

                $scope.reload.wip = false;

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
        $scope.autoupdate.run();
    };

    $scope.buttonAutoexpose = function() {
        console.info("Enable autoexposure");
        $scope.exposure.auto = true;
        $scope.autoupdate.run();
    };

    $scope.buttonSaveAs = function() {
        console.info("Save as...");
        var savePath = remote.dialog.showSaveDialog({
            title: "Save Image As PNG",
            filters: [
                {
                    name: "PNG Image",
                    extensions: [".png"]
                }
            ]
        });
        console.info("Savepath is " + savePath);
        fs.copyFileSync(
            toControlFile($scope.d.activePreview + ".png"),
            savePath
        );
    };

    // ========================================================================
    // Auto update loop

    $scope.autoupdate = {};
    $scope.autoupdate.enable = true;
    $scope.autoupdate.running = false;

    $scope.autoupdate.run = function() {

        if ($scope.autoupdate.running) {
            return;
        }

        $scope.autoupdate.running = true;

        console.info("Autoupdate");

        $scope.reloadImage(function() {

            $scope.autoupdate.running = false;

            if ($scope.autoupdate.enable) {
                setTimeout(function() {
                    $scope.autoupdate.run();
                }, 3000);
            } else {
                return;
            }

        });

    };

    $scope.autoupdate.run();

    // ========================================================================
    // Progress

    $scope.progress = {};
    $scope.progress.finish = false;
    $scope.progress.dir = 0;
    $scope.progress.ind = 0;

    // ========================================================================
    // Startup

    $scope.startupFunc = function() {
        performStartupActions();
        priv.startPbrt(
            // onPbrtExit
            function(code, signal) {

            },
            // onRenderFinish
            function() {
                $scope.progress.ind = 100;
                $scope.progress.dir = 100;
                $scope.$apply();
                // Stop autoupdate after 10 seconds
                setTimeout(function() {
                    console.info("Render finished, disabling autoupdate");
                    $scope.autoupdate.enable = false;
                }, 10000);
            },
            // onIndirectProgress
            function(progress) {
                $scope.progress.ind = 100 * progress;
                $scope.$apply();
            },
            // onDirectProgress
            function(progress) {
                $scope.progress.ind = 100;
                $scope.progress.dir = 100 * progress;
                $scope.$apply();
            }
        );
    };

    $scope.startupFunc();

});
