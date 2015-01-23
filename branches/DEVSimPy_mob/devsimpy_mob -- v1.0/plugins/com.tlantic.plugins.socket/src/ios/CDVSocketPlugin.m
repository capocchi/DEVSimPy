#import "CDVSocketPlugin.h"
#import "Connection.h"
#import <cordova/CDV.h>

@implementation CDVSocketPlugin : CDVPlugin

- (NSString*) buildKey : (NSString*) host : (int) port {
    NSString* tempHost = [host lowercaseString];
    NSString* tempPort = [NSString stringWithFormat : @"%d", port];
    
    return  [[tempHost stringByAppendingString : @":"] stringByAppendingString:tempPort];
}

- (void) connect : (CDVInvokedUrlCommand*) command {
    // Validating parameters
    if ([command.arguments count] < 2) {
        
        // Triggering parameter error
        CDVPluginResult* result = [CDVPluginResult
                                   resultWithStatus : CDVCommandStatus_ERROR
                                   messageAsString  : @"Missing arguments when calling 'connect' action."];
        
        [self.commandDelegate
            sendPluginResult : result
            callbackId : command.callbackId
         ];
    } else {
        // Checking connection pool
        if (!pool) {
            self->pool = [[NSMutableDictionary alloc] init];
        }
        
        // Running in background to avoid thread locks
        [self.commandDelegate runInBackground:^{
            
            CDVPluginResult* result = nil;
            Connection* socket = nil;
            NSString* key = nil;
            NSString* host = nil;
            int port = 0;
            
            // Opening connection and adding into pool
            @try {
                // Preparing parameters
                host = [command.arguments objectAtIndex : 0];
                port = [[command.arguments objectAtIndex : 1] integerValue];
                key = [self buildKey : host : port];
                
                // Checking existing connections
                if ([pool objectForKey : key]) {
                    NSLog(@"Recovered connection with %@", key);
                    result = [CDVPluginResult
                              resultWithStatus : CDVCommandStatus_OK
                              messageAsString : key];
                } else {
                    NSLog(@"Opened connection with %@", key);

                    // Creating connection
                    socket = [[Connection alloc] initWithNetworkAddress:host :port];
                    [socket setDelegate:self];
                    [socket open];
                    
                    // Adding to pool
                    [self->pool setObject:socket forKey:key];
                    
                    // Formatting success response
                    result = [CDVPluginResult
                              resultWithStatus :
                              CDVCommandStatus_OK messageAsString : key];
                }
            }
            @catch (NSException *exception) {
                NSLog(@"Exception: %@", exception);
                result = [CDVPluginResult
                          resultWithStatus : CDVCommandStatus_ERROR
                          messageAsString  : @"Unexpected exception when executing 'connect' action."];
            }
            
            // Returns the Callback Resolution
            [self.commandDelegate sendPluginResult  : result
                                         callbackId : command.callbackId];
        }];
    }
}

- (void) isConnected : (CDVInvokedUrlCommand *) command {
    // Validating parameters
    if ([command.arguments count] < 1) {
        
        // Triggering parameter error
        CDVPluginResult* result = [CDVPluginResult
                                   resultWithStatus : CDVCommandStatus_ERROR
                                   messageAsString  : @"Missing arguments when calling 'isConnected' action."];
        
        [self.commandDelegate
            sendPluginResult:result
            callbackId:command.callbackId
         ];
        
    } else {
        
        // running in background to avoid thread locks
        [self.commandDelegate runInBackground : ^{
            
            CDVPluginResult* result= nil;
            Connection* socket = nil;
            NSString* key = nil;
            
            @try {
                // Preparing parameters
                key = [command.arguments objectAtIndex:0];
                
                // Getting connection from pool
                socket = [pool objectForKey:key];
                
                // Checking if socket was not found and his conenctivity
                if (socket == nil) {
                    NSLog(@"Connection not found");
                    result = [CDVPluginResult
                              resultWithStatus : CDVCommandStatus_ERROR
                              messageAsString  : @"No connection found with host."];
                } else {
                    NSLog(@"Checking data connection...");
                    
                    // Formatting success response
                    result = [CDVPluginResult
                              resultWithStatus : CDVCommandStatus_OK
                              messageAsBool : [socket isConnected]];
                }
            }
            @catch (NSException *exception) {
                NSLog(@"Exception: %@", exception);
                result = [CDVPluginResult
                          resultWithStatus : CDVCommandStatus_ERROR
                          messageAsString  : @"Unexpected exception when executon 'isConnected' action."];
            }
            
            // Returning callback resolution
            [self.commandDelegate
                sendPluginResult : result
                callbackId:command.callbackId
             ];
        }];
    }
}

- (BOOL) disposeConnection : (NSString *) key {
    Connection* socket = nil;
    BOOL result = NO;
    
    @try {
        // Getting connection from pool
        socket = [pool objectForKey : key];
        
        // Closing connection
        if (socket) {
            [pool removeObjectForKey : key];
            
            if ([socket isConnected])
                [socket close];
            
            socket = nil;
            
            NSLog(@"Closed connection with %@", key);
        } else
           NSLog(@"Connection %@ already closed!", key);
        
        // Setting success
        result = YES;
    }
    @catch (NSException *exception) {
        NSLog(@"Exception when closing connection: %@", exception);
        result = NO;
    }
    @finally {
        return result;
    }
}

- (void) disconnect : (CDVInvokedUrlCommand*) command {
    // Validating parameters
    if ([command.arguments count] < 1) {
        // Triggering parameter error
        CDVPluginResult* result = [CDVPluginResult
                                   resultWithStatus : CDVCommandStatus_ERROR
                                   messageAsString  : @"Missing arguments when calling 'disconnect' action."];
        
        [self.commandDelegate sendPluginResult:result callbackId:command.callbackId];
    } else {
        // Running in background to avoid thread locks
        [self.commandDelegate runInBackground : ^{
            
            CDVPluginResult* result= nil;
            NSString *key = nil;
            
            @try {
                // Preparing parameters
                key = [command.arguments objectAtIndex : 0];

                // Closing socket
                if ([self disposeConnection : key])
                    result = [CDVPluginResult resultWithStatus : CDVCommandStatus_OK];
                else
                    result = [CDVPluginResult
                              resultWithStatus : CDVCommandStatus_ERROR
                              messageAsString  : @"Unable to close connection!"];
            }
            @catch (NSException *exception) {
                NSLog(@"Exception: %@", exception);
                result = [CDVPluginResult
                            resultWithStatus : CDVCommandStatus_ERROR
                            messageAsString  : @"Unexpected exception when executing 'disconnect' action."];
            }
            
            // Returns the Callback Resolution
            [self.commandDelegate sendPluginResult:result callbackId:command.callbackId];
        }];
    }
}

- (void) disconnectAll: (CDVInvokedUrlCommand *) command {
    // Running in background to avoid thread locks
    [self.commandDelegate runInBackground:^{
       
        CDVPluginResult* result = nil;
        Connection * socket = nil;
        BOOL partial = NO;
        
        @try {
            
            // Iterating connection pool
            for (id key in pool) {
                socket = [pool objectForKey : key];
                
                // Try to close it
                if (![self disposeConnection : key]) {
                    // If no success, need to set as partial disconnection
                    partial = YES;
                }
            }
            
            // Formatting result
            if (partial)
                result = [CDVPluginResult
                          resultWithStatus : CDVCommandStatus_ERROR
                          messageAsString  : @"Some connections could not be closed."];
             else
                result = [CDVPluginResult resultWithStatus : CDVCommandStatus_OK];
        }
        @catch (NSException *exception) {
            NSLog(@"Exception: %@", exception);
            result = [CDVPluginResult
                      resultWithStatus : CDVCommandStatus_ERROR
                      messageAsString  : @"Unexpected exception when executing 'disconnectAll' action."];
        }
        @finally {
            // Returns the Callback Resolution
            [self.commandDelegate
                sendPluginResult : result
                callbackId : command.callbackId];
        }
    }];
}

- (void) send: (CDVInvokedUrlCommand *) command {
    
    // Validating parameters
    if ([command.arguments count] < 2) {
        // Triggering parameter error
        CDVPluginResult* result = [CDVPluginResult
                                   resultWithStatus : CDVCommandStatus_ERROR
                                   messageAsString  : @"Missing arguments when calling 'send' action."];
        
        [self.commandDelegate
            sendPluginResult : result
            callbackId:command.callbackId
         ];
        
    } else {
        
        // Running in background to avoid thread locks
        [self.commandDelegate runInBackground : ^{
            
            CDVPluginResult* result= nil;
            Connection* socket = nil;
            NSString* data = nil;
            NSString* key = nil;
            
            @try {
                // Preparing parameters
                key = [command.arguments objectAtIndex : 0];
                
                // Getting connection from pool
                socket = [pool objectForKey : key];
                
                // Checking if socket was not found and his conenctivity
                if (socket == nil) {
                    NSLog(@"Connection not found");
                    result = [CDVPluginResult
                              resultWithStatus : CDVCommandStatus_ERROR
                              messageAsString  : @"No connection found with host."];
                    
                } else if (![socket isConnected]) {
                    NSLog(@"Socket is not connected.");
                    result = [CDVPluginResult
                                resultWithStatus : CDVCommandStatus_ERROR
                                messageAsString  : @"Invalid connection with host."];
                } else {
                    // Writting on output stream
                    data = [command.arguments objectAtIndex : 1];
                    
                    NSLog(@"Sending data to %@ - %@", key, data);
                    
                    [socket write:data];
                
                    // Formatting success response
                    result = [CDVPluginResult
                              resultWithStatus : CDVCommandStatus_OK
                              messageAsString : key];
                }
            }
            @catch (NSException *exception) {
                NSLog(@"Exception: %@", exception);
                result = [CDVPluginResult
                          resultWithStatus : CDVCommandStatus_ERROR
                          messageAsString  : @"Unexpected exception when executon 'send' action."];
            }
            
            // Returning callback resolution
            [self.commandDelegate sendPluginResult : result callbackId : command.callbackId];
        }];
    }
}

- (void) sendMessage :(NSString *)host :(int)port :(NSString *)chunk {
    
    // Handling escape chars
    NSMutableString *data = [NSMutableString stringWithString : chunk];
    [data replaceOccurrencesOfString   : @"\n"
                            withString : @"\\n"
                            options    : NSCaseInsensitiveSearch
                            range      : NSMakeRange(0, [data length])];
    
    // Relay to webview
    NSString *receiveHook = [NSString stringWithFormat : @"window.tlantic.plugins.socket.receive('%@', %d, '%@', '%@' );",
                                host, port, [self buildKey : host : port], [NSString stringWithString : data]];
    
    [self writeJavascript:receiveHook];
}

@end