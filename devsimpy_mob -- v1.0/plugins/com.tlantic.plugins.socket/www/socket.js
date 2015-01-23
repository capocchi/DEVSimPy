/* global module, require, document */
var exec = require('cordova/exec');

//
function Socket(){
    'use strict';

    this.receiveHookName = 'SOCKET_RECEIVE_DATA_HOOK';      // *** Event name to act as "hook" for data receiving
    this.pluginRef = 'Socket';                              // *** Plugin reference for Cordova.exec calls
}

//
Socket.prototype.connect = function (successCallback, errorCallback, host, port) {
    'use strict';
    exec(successCallback, errorCallback, this.pluginRef, 'connect', [host, port]);
};

//
Socket.prototype.disconnect = function (successCallback, errorCallback, connectionId) {
    'use strict';
    exec(successCallback, errorCallback, this.pluginRef, 'disconnect', [connectionId]);
};

//
Socket.prototype.disconnectAll = function (successCallback, errorCallback) {
    'use strict';
    exec(successCallback, errorCallback, this.pluginRef, 'disconnectAll', []);
};
               
//
Socket.prototype.isConnected = function (connectionId, successCallback, errorCallback) {
    'use strict';
    exec(successCallback, errorCallback, this.pluginRef, 'isConnected', [connectionId]);
}

//
Socket.prototype.send = function (successCallback, errorCallback, connectionId, data) {
    'use strict';
    exec(successCallback, errorCallback, this.pluginRef, 'send', [connectionId, typeof data == 'string' ? data : JSON.stringify(data)]);
};

//
Socket.prototype.receive = function (host, port, connectionId, chunk) {
    'use strict';

    var evReceive = document.createEvent('Events');
    
    evReceive.initEvent(this.receiveHookName, true, true);
    evReceive.metadata = {
        connection: {
            id: connectionId,
            host: host,
            port: port,
        },
        data: chunk
    };

    document.dispatchEvent(evReceive);
};
module.exports = new Socket();
