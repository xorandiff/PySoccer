from twisted.internet import protocol, reactor, endpoints

PORT = 1838

class PySoccerServer(protocol.Protocol):
    def __init__(self, factory):
        self.factory: PySoccerServerFactory = factory
        self.opponent: PySoccerServer | None = None
    
    def connectionMade(self):
        self.factory.numProtocols += 1
        print(f"New client connected (IPv4: {self.transport.getHost().host}, total connections: {self.factory.numProtocols})")
    
    def connectionLost(self, reason):
        self.factory.numProtocols -= 1
    
    def dataReceived(self, data):
        message = data.decode()
        print(f"Received from client: {message}")
        if self.opponent:
            self.opponent.send(message)
        if message == "JOIN":
            if len(self.factory.playerQueue):
                self.opponent = self.factory.playerQueue.pop(0)
                self.opponent.opponent = self
                
                self.send("JOINED")
                self.opponent.send("JOINED")
            else:
                self.factory.playerQueue.append(self)

    def send(self, message: str):
        self.transport.write(str.encode(message))

class PySoccerServerFactory(protocol.Factory):
    def __init__(self):
        protocol.Factory.__init__(self)
        self.numProtocols = 0
        self.playerQueue = []
    
    def buildProtocol(self, addr):
        return PySoccerServer(self)

endpoints.TCP4ServerEndpoint(reactor, PORT).listen(PySoccerServerFactory())
print(f"PySoccer Server started listening on port {PORT}")

reactor.run()
