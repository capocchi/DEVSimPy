#import "Connection.h"

@implementation Connection: NSObject

- (id) initWithNetworkAddress : (NSString *) targetHost : (int) targetPort {
    self = [super init];
    if (self) {
        _host = targetHost;
        _port = targetPort;
        connected = NO;
    }
    return self;
}

- (void) setDelegate : (id<ConnectionDelegate>) callbackRef {
    _hook = callbackRef;
}

- (BOOL) isConnected {
    return connected;
 }

- (void) open {
    // Init network communication settings
    CFReadStreamRef readStream;
    CFWriteStreamRef writeStream;
    
    // Opening connection
    CFStreamCreatePairWithSocketToHost(NULL, (__bridge CFStringRef)_host, _port, &readStream, &writeStream);
    
    // Configuring input stream
    reader = objc_retainedObject(readStream);
    [reader setDelegate:self];
    [reader scheduleInRunLoop:[NSRunLoop mainRunLoop] forMode:NSDefaultRunLoopMode];
    [reader open];
    
    // Configuring output stream
    writer = objc_retainedObject(writeStream);
    [writer setDelegate:self];
    [writer scheduleInRunLoop:[NSRunLoop currentRunLoop] forMode:NSDefaultRunLoopMode];
    [writer open];
}

- (void) close {
    // Closing output stream
    [writer close];
    [writer removeFromRunLoop:[NSRunLoop currentRunLoop] forMode:NSDefaultRunLoopMode];
    [writer setDelegate:nil];
    writer = nil;
    
    // Closing input stream
    [reader close];
    [reader removeFromRunLoop:[NSRunLoop mainRunLoop] forMode:NSDefaultRunLoopMode];
    [reader setDelegate:nil];
    reader = nil;
}

- (void) write : (NSString *) data {
    NSData *chunk = [[NSData alloc] initWithData : [data dataUsingEncoding : NSASCIIStringEncoding]];
    [writer write : [chunk bytes] maxLength : [chunk length]];
}

- (void) stream : (NSStream *) theStream handleEvent : (NSStreamEvent) streamEvent {
	switch (streamEvent) {
		case NSStreamEventOpenCompleted:
			NSLog(@"Stream opened!");
            connected = YES;
			break;
            
        // Data receiving
		case NSStreamEventHasBytesAvailable:
            if (theStream == reader) {
                uint8_t buffer[10240];
                NSInteger len;
                
                while ([reader hasBytesAvailable]) {
                    len = [reader read : buffer maxLength : sizeof(buffer)];
                    
                    if (len > 0) {
                        
                        NSString *chunk = [[NSString alloc] initWithBytes : buffer
                                                                   length : len
                                                                 encoding : NSASCIIStringEncoding];
                        
                        if (nil != chunk) {
                            NSLog(@"Received data: %@", chunk);
                            [_hook sendMessage : _host : _port : chunk];
                        }
                    }
                }
            }
            break;
            
        case NSStreamEventErrorOccurred:
            NSLog(@"Cannot connect to the host!");
            connected = NO;
            break;
            
        case NSStreamEventEndEncountered:
            NSLog(@"Stream closed!");
            connected = NO;
            break;
            
        default:
            NSLog(@"Unknown event!");
    }
}

@end