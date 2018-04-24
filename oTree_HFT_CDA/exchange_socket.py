try:
    import socket
except ImportError:
    raise ImportError("import socket moudle")
    exit(1)




class Exchange_Socket:
    def __init__(self, sock=None):
        self.MSGLEN = 0

        if sock is None:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        else:
            self.sock = sock

    def connect(self, host, port):
        self.sock.connect((host, port))


    def send(self, msg):
        if msg[0] == 'U':
            self.MSGLEN = 47
        elif msg[0] == 'O':
            self.MSGLEN = 49
        elif msg[0] == 'X':
            self.MSGLEN = 19
            
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        chunks = []
        bytes_recd = 0
        while bytes_recd < self.MSGLEN:
            chunk = self.sock.recv(min(len(msg) - bytes_recd, 2048))
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks.append(chunk)
            bytes_recd = bytes_recd + len(chunk)
        return b''.join(chunks)