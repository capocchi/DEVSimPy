cdv-socket-plugin
=================

Cordova TCP Socket Plugin


Follows the [Cordova Plugin spec](https://github.com/apache/cordova-plugman/blob/master/plugin_spec.md), so that it works with [Plugman](https://github.com/apache/cordova-plugman)

## Cordova/Phonegap Support ##

This plugin was tested and qualified using Cordova 3.4 adn Cordova 3.5. The demo app contains implementation for Android, iOS and Windows 8. You can check that out at [demo app repository](https://github.com/Tlantic/SocketPluginDemo)

## Adding the plugin ##

To add the plugin, just run the following command through cordova CLI:

```
cordova plugin add com.tlantic.plugins.socket
```

## Using the plugin ##

The plugin creates a "Socket" object exposed on window.tlantic.plugins.socket. The following methods can be accessed:

* connect: opens a socket connection;
* disconnect: closes a socket connection;
* disconnectAll: closes ALL opened connections;
* send: send data using a given connection;
* isConnected: returns a boolean falg representing socket connectivity status;
* receive: callback used by plugin's native code. Can be override by a custom implementation.

### Connection ID

Since v0.3 version, the plugin started to return a connection id after calling connect method. This is must be used for all operationg regarding the given connection, like disconnect, send and isConnected.

The current implementation defines the connection id as "<host>:<port>", but is strongly recommended for your app: DO NOT PARSE THIS! Thist conenction id was designes to avoid having your app informing the host and port all the time. So, is not safe assume all versions of this plugin will keep this format. We are free to change it in the future as needed (if finding a better option). Keep that in mind...

### connect (successCallback, errorCallback, host, port)

Example:

```
window.tlantic.plugins.socket.connect(
  function (connectionId) {
    console.log('worked! This is the connection ID: ', connectionId);  
  },
  
  function () {
    console.log('failed!');
  },
  '192.168.2.5',
  18002
);
```

### disconnect (successCallback, errorCallback, connectionId)

Disconnects any connection opened for a given connection.

Example:

```
window.tlantic.plugins.socket.disconnect(
  function () {
    console.log('worked!');  
  },
  
  function () {
    console.log('failed!');
  },
  '192.168.2.5:18002'
);
```

### disconnectAll (successCallback, errorCallback)

Example:

```
window.tlantic.plugins.socket.connect(
  function () {
    console.log('worked!');  
  },
  
  function () {
    console.log('failed!');
  }
);
```

### send (successCallback, errorCallback, connectionId, data)

Sends information and calls success callback if information was send and does not wait for any response. To check how to receive data, please see the item below.

Example:

```
window.tlantic.plugins.socket.send(
  function () {
    console.log('worked!');  
  },
  
  function () {
    console.log('failed!');
  },
  '192.168.2.5:18002',
  'This is the data i want to send!'
);
```

### isConnected (connectionId, successCallback, errorCallback)

Returns a boolean value representing the connection status. True, if socket streams are opened and false case else.
Both values are supposed to be returned through successCallback. The error callback is called only when facing errors due the check process.

Example:

```
window.tlantic.plugins.socket.isConnected(
  '192.168.2.5:18002',
  function () {
    console.log('worked!');  
  },
  
  function () {
    console.log('failed!');
  }
);
```

### receive (host, port, connectionId, data)

This method is a callback invoked by native code through webview capabilities. You can replace this method by your own implementation. Even this way, the default implementation dispatches a JS event which can be catched listening that event. Here it goes a proper implementation regarding default method behavior:

```
document.addEventListener(window.tlantic.plugins.socket.receiveHookName, function (ev) {
  console.log(ev.metadata.host);    // host who sent the data
  console.log(ev.metadata.port);    // sender port
  console.log(ev.metadata.id);      // connection id
  console.log(ev.metadata.data);    // received data
});
```

## License terms

    Cordova TCP Socket Plugin
    Copyright (C) 2014  Tlantic SI

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>
