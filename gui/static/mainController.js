var mainApp = angular.module("mainApp", []);

mainApp.controller("main_controller", function($scope) {

    $scope.title = "pbrt v3 IILE";

    $scope.buttonCombined = function() {
        var imgPath = "/home/gj/git/pbrt-v3-scenes-extra/staircase2/TungstenRender.png";
        loadImage("img_main", imgPath);
    };

});
