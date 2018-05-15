var mainApp = angular.module("mainApp", []);

mainApp.controller("main_controller", function($scope) {

    $scope.title = "pbrt v3 IILE";

    $scope.d = {};

    // Preview images =========================================================

    $scope.d.activePreview = "out_indirect.png";

    $scope.buttonCombined = function() {
        $scope.d.activePreview = "out_combined.png";
        $scope.reloadImage();
    };

    $scope.buttonIndirect = function() {
        $scope.d.activePreview = "out_indirect.png";
        $scope.reloadImage();
    };

    $scope.buttonDirect = function() {
        $scope.d.activePreview = "out_direct.png";
        $scope.reloadImage();
    };

    $scope.reloadImage = function() {
        loadImage("img_main", toControlFile($scope.d.activePreview));
    };

    // Exposure controls ======================================================

    $scope.exposure = 0;

    $scope.buttonExposureApply = function() {
        console.info("Updating exposure control");
        data.exposure = $scope.exposure;
        controlWriteExposure();
    };

    // Status info ============================================================

    $scope.status = "Idle";

    // ========================================================================
    // Auto update loop
    setInterval(function() {
        console.info("Reloading image...");
        // Reload current image
        $scope.reloadImage();
        $scope.status = data.pbrtStatus;
        $scope.$apply();
    }, 1500); // Every 5 seconds

});
