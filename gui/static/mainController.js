var mainApp = angular.module("mainApp", []);

mainApp.controller("main_controller", function($scope) {

    $scope.title = "pbrt v3 IILE";

    $scope.d = {};

    // Preview images =========================================================

    $scope.d.activePreview = "out_indirect";

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

});
