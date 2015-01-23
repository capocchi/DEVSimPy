    /* global console, exports, require */
    'use strict';

    var Connection = require('com.tlantic.plugins.socket.Connection');

    // connection pool
    exports.pool = [];

    // builds connectionId
    exports.buildKey = function (host, port) {
        return host.toLowerCase() + ':' + port;
    };

    // establish TCP connection with remote endpoint 
    exports.connect = function (win, fail, args) {

        var host, port, key, socket;

        // validating parameters
        if (args.length !== 2) {
            fail('Missing arguments for "connect" action.');
            return;

        } else {

            // building connection key
            host = args[0];
            port = args[1];
            key = exports.buildKey(host, port);

            // trying to recover an existing connection
            if (exports.pool[key]) {
                console.log('Recovered connection with ', key);
                win(key);
                return;

            } else {

                // creating new connection;
                socket = new Connection(host, port);
                socket.onReceive = exports.sendMessage;

                // opening stream
                socket.connect(function () {

                    // adding to pool
                    console.log('Connection with ', key, ' opened successfully!');
                    exports.pool[key] = socket;

                    // returning key as success sign
                    win(key);
                }, fail);
            }
        }

    };

    // closes TCP connection and releases network resources
    exports.disposeConnection = function (socket) {

        var result = false;

        try {
            socket.close();
            result = true;

        } catch (e) {
            console.log('Unable to close connection!');
            result = false;

        } finally {
            return result;
        }
    };

    // closes a specific connection
    exports.disconnect = function (win, fail, args) {

        var key, socket;

        // validating parameters
        if (args.length !== 1) {
            fail('Missing arguments for "disconnect" action.');
            return;
        } else {

            // retrieving existing connection
            key = args[0];
            socket = exports.pool[key];
            if (!socket) {
                fail('Connection ' + key + ' not found!');
                return;
            } else {

                // removing from pool and closing socket
                exports.pool[key] = undefined;

                if (exports.disposeConnection(socket)) {
                    win();
                } else {
                    fail('Unable to close connection with ' + key);
                }

                return;
            }
        }

    };

    // closes all active connections
    exports.disconnectAll = function (win, fail) {

        var socket, partial = false;

        console.log('Preparing to disconnect all connections:');

        // checking all connections from pool
        for (var key in exports.pool) {

            // retrieving existing socket
            console.log('- Closing ', key, ' ...');
            socket = exports.pool[key];

            // disposing socket
            if (!exports.disposeConnection(socket)) {
                partial = true;
                console.log('- Unable to close ', key);
            }

            // removing from pool
            exports.pool[key] = undefined;
        }


        // returning based on all results
        if (partial) {
            fail('Some connections could not be closed!');
        } else {
            win();
        }
    };

    // writes data in outputStream
    exports.send = function (win, fail, args) {

        var key, data, socket;

        // validating parameters
        if (args.length !== 2) {
            fail('Missing arguments for "disconnect" action.');
            return;
        } else {

            // retrieving existing connection
            key = args[0];
            data = args[1];

            socket = exports.pool[key];
            if (!socket) {
                fail('Connection ' + key + ' not found!');
                return;
            } else {

                // flushing information
                socket.write(data, win, fail);

            }
        }

    };

    // callback to receive data written on socket inputStream
    exports.sendMessage = function (host, port, data) {

        var key = exports.buildKey(host, port);
    
        window.tlantic.plugins.socket.receive(host, port, key, data);
    };

    require('cordova/windows8/commandProxy').add('Socket', exports);