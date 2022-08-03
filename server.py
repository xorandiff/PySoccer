from twisted.internet import protocol, reactor, endpoints
from twisted.protocols.basic import LineReceiver

PORT = 1838

class PySoccerServer(LineReceiver):
    def __init__(self, factory):
        self.factory: PySoccerServerFactory = factory
        self.opponent: PySoccerServer | None = None
    
    def connectionMade(self):
        self.factory.numProtocols += 1
        print(f"New client connected (IPv4: {self.transport.getHost().host}, total connections: {self.factory.numProtocols})") # type: ignore[attr-defined]
    
    def connectionLost(self, reason):
        self.factory.numProtocols -= 1
        
        # Notify player opponent (if exist) about leaving the game
        if self.opponent:
            self.opponent.send("LEFT")
        
        # Remove current player from game queue, if present
        if self in self.factory.playerQueue:
            self.factory.playerQueue.remove(self)
    
    def lineReceived(self, line):
        message = line
        print(f"Received from client: {message}")
        
        # Pass data to player's opponet (if exist)
        if self.opponent:
            self.opponent.send(message)
            
        # Handle join game request from player
        if message == "JOIN":
            if len(self.factory.playerQueue):
                # If waiting queue is nonempty, then pair with player from queue
                self.opponent = self.factory.playerQueue.pop(0)
                self.opponent.opponent = self
                
                self.send("JOINED_2")
                self.opponent.send("JOINED_1")
            else:
                # If waiting queue is empty, add player to queue
                self.factory.playerQueue.append(self)      
        elif message == "PING":
            self.send("PONG")

    def send(self, line: str):
        self.sendLine(line)

class PySoccerServerFactory(protocol.Factory):
    def __init__(self):
        protocol.Factory.__init__(self)
        self.numProtocols = 0
        self.playerQueue = []
    
    def buildProtocol(self, addr):
        return PySoccerServer(self)

endpoints.TCP4ServerEndpoint(reactor, PORT).listen(PySoccerServerFactory())
print(f"PySoccer Server started listening on port {PORT}")

reactor.run() # type: ignore[attr-defined]
