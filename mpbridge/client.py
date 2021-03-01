import trio
from itertools import count


class Client:
    counter = count()
    protocol = 'NON'

    def __init__(self):
        self.unpaired = trio.Semaphore(0, max_value=1)
        self.done = trio.Event()
        self.ident = next(self.counter)

    def __str__(self):
        return self.protocol + ':' + str(self.ident)

    def send_all(self, data):
        raise NotImplementedError

    def __aiter__(self):
        raise NotImplementedError


class TCPClient(Client):
    protocol = 'TCP'
    def __init__(self, stream):
        super().__init__()
        self.stream = stream

    async def send_all(self, data):
        await self.stream.send_all(data)

    def __aiter__(self):
        return self.stream


class USBClient(Client):
    protocol = 'USB'
    def __init__(self, port):
        super().__init__()
        self.port = port

    async def __aiter__(self):
        try:
            while True:
                yield await self.port.receive()
        except Exception:
            return

    async def send_all(self, data):
        await self.port.send(data)
