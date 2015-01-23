@protocol ConnectionDelegate <NSObject>

- (void) sendMessage : (NSString *) host : (int)port : (NSString *) chunk;

@end

@interface Connection : NSObject <NSStreamDelegate> {
@private
    NSInputStream *reader;
    NSOutputStream *writer;
    BOOL connected;
}

@property NSString *host;
@property int port;
@property (nonatomic, weak) id<ConnectionDelegate> hook;

- (id) initWithNetworkAddress : (NSString*) targetHost : (int) targetPort;
- (void) setDelegate : (id<ConnectionDelegate>) callbackRef;
- (BOOL) isConnected;
- (void) open;
- (void) close;
- (void) write : (NSString*) data;

- (void) stream : (NSStream *) theStream handleEvent : (NSStreamEvent) streamEvent;

@end