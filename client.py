from twisted.internet.protocol import Protocol, ClientFactory
from twisted.internet import reactor
from multiprocessing import Process, Pipe
from sys import stdout
import threading

HOST = "127.0.0.1"
PORT = 1838

class PySoccerClient(Protocol):
        def __init__(self, conn):
            Protocol.__init__(self)
            self.conn = conn

        def dataReceived(self, data):
            stdout.write(str(data))
            self.conn.send(str(data))
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
        print('Lost connection to game server.  Reason:', reason)
        self.conn.send("RECONNECTING")
        connector.connect()

    def clientConnectionFailed(self, connector, reason):
        print('Connection to game server failed. Reason:', reason)
        self.conn.send("CONNECTION_LOST")
        
    def _loop(self):
        while True:
            message = self.conn.recv()
            print(f"Received message to sen: {message}")
            self.c
            
    def start_loop(self):
        threading.Thread(target=self._loop, daemon=True).start()
        
class ClientProcess(Process):
    def __init__(self, conn):
        Process.__init__(self)
        self.name = "Client"
        self.daemon = True
        self.conn = conn
    
    def run(self):
        clientFactory = PySoccerClientFactory(self.conn)
        reactor.connectTCP(HOST, PORT, clientFactory) # type: ignore[attr-defined]
        clientFactory.start_loop()
        reactor.run() # type: ignore[attr-defined]