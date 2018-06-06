priv.time = {};

// Starts the timer and returns a timekeeping object
priv.time.start = function() {
    return new Date();
}

// Calculates time elapsed from timekeeping object
// in milliseconds
priv.time.stop = function(startObject) {
    var now = new Date();
    return now.getTime() - startObject.getTime();
}