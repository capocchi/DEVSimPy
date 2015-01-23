/* global module, Windows, console, require */
'use strict';

     // Connection Class Definition
    module.exports = function Connection(host, port) {
        var self = this,
        mustClose = false,
        rawSocket,
        hostname,
        service,
        reader;

        // init - constructor
        self.init = function Initialize(host, port) {

            // setting instance properties
            self.host = host;
            self.port = port;

            // creating network objects
            hostname = new Windows.Networking.HostName(host);
            service = port.toString();
            rawSocket = new Windows.Networking.Sockets.StreamSocket();
        };

        // Socket connect
        self.connect = function Connect(cbSuccess, cbFailure) {
            rawSocket.connectAsync(hostname, service).done(function onConnect() {

                try {
                    // opening inputStream for reading
                    reader = new Windows.Storage.Streams.DataReader(rawSocket.inputStream);
                    reader.inputStreamOptions = Windows.Storage.Streams.InputStreamOptions.partial;

                    // start reading
                    self.startReader();

                    // returning success
                    cbSuccess();
                } catch (e) {
                    console.log('Unable to establish connection: ', e);
                    cbFailure(e);
                    self.close();
                }

            }, cbFailure);
        };

        // Socket closure
        self.close = function Close() {
            mustClose = true;
            rawSocket.close();
        };

        // Socket write
        self.write = function Write(data, cbSuccess, cbFailure) {

            // preparing for sending
            var writer = new Windows.Storage.Streams.DataWriter(rawSocket.outputStream),
                bufSize = writer.measureString(data); // Gets the UTF-8 string length.

                writer.writeInt32(bufSize);
                writer.writeString(data);

                console.log('Sending ', data);

            // flushing information
            writer.storeAsync().done(function () {

                // detaching outputStream and with success
                writer.detachStream();
                cbSuccess();

            }, cbFailure);

        };

        // Socket start receiving data
        self.startReader = function startReader() {

            // starting to read Async
            return reader.loadAsync(99999999).then(function (bytesRead) {

                // reading buffer
                var chunk;

                try {
                    chunk = reader.readString(reader.unconsumedBufferLength);

                    // handling data receiving
                    if (bytesRead !== 0 && !mustClose) {
                        self.onReceive(self.host, self.port, chunk);
                    }

                    // checking reading ending
                    if (mustClose) {
                        return;
                    } else {
                        return startReader();
                    }
                } catch (e) {
                    console.log('Unexpected connection closure with ', self.host, ' on port ', self.port, ': ', e);
                    mustClose = true;
                    return;
                }
            });
        };

        // Socket data receiving
        self.onReceive = function onReceive() {
            console.log('no callback defined for Socket.OnReceive!');
        };

        // initializing object instance
        self.init(host, port);
    };

    // exporting module
    require('cordova/windows8/commandProxy').add('Connection', module);