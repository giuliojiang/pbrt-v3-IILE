const {app, BrowserWindow} = require('electron')
const path = require('path')
const url = require('url')

global.shd = {
    argv: process.argv,
    console: console,
    pbrtProc: null,
    win: null
}

function createWindow () {
    // Create the browser window.
    win = new BrowserWindow({width: 1280, height: 720})

    // and load the index.html of the app.
    win.loadURL(url.format({
        pathname: path.join(__dirname, "static", 'index.html'),
        protocol: 'file:',
        slashes: true
    }));

    global.shd.win = win;

}

app.on('ready', createWindow);

