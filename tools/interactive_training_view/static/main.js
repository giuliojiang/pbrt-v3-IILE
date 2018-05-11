var mainApp = angular.module("mainApp", []);

mainApp.controller("main_controller", function($scope) {

    var priv = {};

    $scope.d = {};

    $scope.d.examples = []; // each example is a
    // {
    //     low: {
    //         l1, ss
    //     },
    //     gauss: {
    //         l1, ss
    //     },
    //     pred: {
    //         l1, ss
    //     }
    // }

    $scope.d.nextNum = 0;

    // ------------------------------------------------------------------------
    // Websocket setup

    var ws = new WebSocket("ws://localhost:32001");

    ws.onopen = function() {
        console.info("Websocket connection opened");
    };

    ws.onmessage = function(evt) {
        var data = evt.data;
        var msgobj = JSON.parse(data);
        priv.handle_ws_message(msgobj);
    };

    ws.onclose = function() {
        console.error("Websocket disconnected");
    }

    priv.handle_ws_message = function(msgobj) {
        console.info("Received a ws message");
        console.info(msgobj);
        var t = msgobj._t;
        if (t == "task_complete") {
            $scope.d.nextNum += 1;
            var anExample = msgobj.example;
            if (!anExample) {
                anExample = {};
            }
            anExample.num = $scope.d.nextNum;
            $scope.d.examples.push(anExample);
            $scope.$apply();
            async.setImmediate(function() {
                priv.loadRow(anExample.num);
            });
        }
    };

    priv.send = function(msgobj) {
        var data = JSON.stringify(msgobj);
        ws.send(data);
    };

    // ------------------------------------------------------------------------
    // Buttons

    $scope.button_load = function() {
        console.info("Load button pressed");
        priv.send({
            _t: "button_load"
        });
    };

    $scope.button_next = function() {
        console.info("Next button pressed");
        priv.send({
            _t: "button_next"
        });
    };

    // ------------------------------------------------------------------------
    // Images

    priv.image_refresh_by_id = function(name, num) {
        var elem_id = name + "_" + num;
        var elem = document.getElementById(elem_id);
        var new_source = name + "?" + new Date().getTime();
        elem.src = new_source;
    };

    priv.loadRow = function(rowNumber) {

        var imgIds = [
            "img_normals",
            "img_distance",
            "img_low",
            "img_gauss",
            "img_pred",
            "img_ground"
        ];
        for (var i = 0; i < imgIds.length; i++) {
            priv.image_refresh_by_id(imgIds[i], rowNumber);
        }
    }

});