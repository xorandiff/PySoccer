from twisted.internet import protocol, reactor, endpoints

PORT = 1838

class PySoccerServer(protocol.Protocol):
    def connectionMade(self):
        print(f"New client connected (IPv4: {self.transport.getHost().host})")
    def dataReceived(self, data):
        self.transport.write(data)

class PySoccerServerFactory(protocol.Factory):
    def buildProtocol(self, addr):
        return PySoccerServer()

endpoints.TCP4ServerEndpoint(reactor, PORT).listen(PySoccerServerFactory())
print(f"PySoccer Server started listening on port {PORT}")

reactor.run()
