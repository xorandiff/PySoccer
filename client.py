from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
from multiprocessing import Process
from sys import stdout

HOST = "127.0.0.1"
PORT = 1838

class PySoccerClient(Protocol):
        def dataReceived(self, data):
            stdout.write(data)

class PySoccerClientFactory(ClientFactory):
    def startedConnecting(self, connector):
        print('Connecting to game server...')

    def buildProtocol(self, addr):
        print('Successfuly connected to game server')
        return PySoccerClient()

    def clientConnectionLost(self, connector, reason):
        print('Lost connection to game server.  Reason:', reason)
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print('Connection to game server failed. Reason:', reason)

class ClientProcess(Process):
    def __init__(self):
        Process.__init__(self)
        self.name = "Client"
        self.daemon = True
    
    def run(self):
        reactor.connectTCP(HOST, PORT, PySoccerClientFactory())
        reactor.run()