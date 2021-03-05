import trio
import click
from anyio_serial import Serial
from serial.tools.list_ports import comports
from serial.serialutil import SerialException

from .client import USBClient, TCPClient, Client

PORT = 0x32b1

pending_client = []

class ClientPairingBroken(Exception):
    pass


async def handle_client(client):
    print(f"client connect {client}")
    while not client.done.is_set():
        if pending_client:
            other_client = pending_client.pop()
            print(f"pairing clients {client}, {other_client}")
            try:
                async with trio.open_nursery() as nursery:
                    nursery.start_soon(handle_client_comms, client, other_client)
                    nursery.start_soon(handle_client_comms, other_client, client)
            except (ClientPairingBroken, trio.MultiError):
                pass
        else:
            print(f"client pending {client}")
            pending_client.append(client)
        await client.unpaired.acquire()
        print(f"client unpaired {client}")
    print(f"client disconnect {client}")


async def handle_client_comms(client, other_client):
    try:
        print(f"comms {client}, {other_client}: starting")
        if isinstance(other_client, Client): # or USBClient, or TCPClient
            print(f"comms _____ -> {other_client}: ", b'32BLMLTI\x01')
            await other_client.send_all(b'32BLMLTI\x01')
        async for data in client:
            print(f"comms {client} -> {other_client}: ", data)
            await other_client.send_all(data)
        print(f"comms {client}, {other_client}: client disconnected")
        client.done.set()
        if isinstance(other_client, Client): # or USBClient, or Client
            print(f"comms _____ -> {other_client}: ", b'32BLMLTI\x00')
            await other_client.send_all(b'32BLMLTI\x00')
        raise ClientPairingBroken
    except Exception as exc:
        print(f"comms {client}, {other_client}: connection broken: {exc!r}")
        raise ClientPairingBroken
    finally:
        print(f"comms {client}, {other_client}: cleaning up")
        client.unpaired.release()


open_ports = set()


async def handle_usb_client(comport):
    try:
        async with Serial(comport) as port:
            await handle_client(USBClient(port))
        open_ports.remove(comport)
    except SerialException:
        pass


async def watch_usb(nursery):
    while True:
        for comport in comports():
            if comport.vid == 0x0483 and comport.pid == 0x5740:
                if comport.device not in open_ports:
                    open_ports.add(comport.device)
                    nursery.start_soon(handle_usb_client, comport.device)
        await trio.sleep(1)


async def handle_tcp_client(stream):
    await handle_client(TCPClient(stream))


async def asyncmain():
    async with trio.open_nursery() as nursery:
        nursery.start_soon(trio.serve_tcp, handle_tcp_client, PORT)
        nursery.start_soon(watch_usb, nursery)


@click.command()
def main():
    trio.run(asyncmain)
