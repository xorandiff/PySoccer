from twisted.internet.protocol import Protocol, ClientFactory
from twisted.protocols.basic import LineReceiver
from twisted.internet import reactor
from multiprocessing import Process
from sys import stdout
import threading

HOST = "146.59.93.188"
PORT = 1838

class PySoccerClient(LineReceiver):
    def __init__(self, conn):
        Protocol.__init__(self)
        self.conn = conn

    def lineReceived(self, line):
        self.conn.send(line)
        
    def connectionMade(self):
        self.start_loop()

    def _loop(self, conn):
        while True:
            message = conn.recv()
            reactor.callLater(0.001, self.sendLine, message)
            
    def start_loop(self):
        threading.Thread(target=self._loop, args=(self.conn,), daemon=True).start()
class PySoccerClientFactory(ClientFactory):
    def __init__(self, conn):
        ClientFactory.__init__(self)
        self.conn = conn
        self.lock = threading.Lock()
    
    def startedConnecting(self, connector):
        print('Connecting to game server...')
        self.conn.send("CONNECTING")

    def buildProtocol(self, addr):
        print('Successfuly connected to game server')
        self.conn.send("CONNECTED")
        return PySoccerClient(self.conn)

    def clientConnectionLost(self, connector, reason):
        print('Lost connection to game server. Reason:', reason)
        self.conn.send("RECONNECTING")
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print('Connection to game server failed. Reason:', reason)
        self.conn.send("DISCONNECTED")

class ClientProcess(Process):
    def __init__(self, conn):
        Process.__init__(self)
        self.name = "Client"
        self.daemon = True
        self.conn = conn
    
    def run(self):
        clientFactory = PySoccerClientFactory(self.conn)
        reactor.connectTCP(HOST, PORT, clientFactory) # type: ignore[attr-defined]
        reactor.run() # type: ignore[attr-defined]