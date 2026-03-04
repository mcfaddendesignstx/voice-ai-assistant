"""
TCP-level TLS proxy: Python on :5173 (firewall-allowed) -> Caddy on :8443 (localhost).
Python.exe already has Windows Firewall allow rules; Caddy does not.
This script just shuffles raw bytes — Caddy handles TLS, HTTP, and WebSocket.
"""
import asyncio, sys

LISTEN_PORT = 5173
CADDY_HOST = '127.0.0.1'
CADDY_PORT = 8443

async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(65536)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except (ConnectionResetError, BrokenPipeError, asyncio.CancelledError):
        pass
    finally:
        writer.close()

async def handle(client_r, client_w):
    try:
        upstream_r, upstream_w = await asyncio.open_connection(CADDY_HOST, CADDY_PORT)
    except Exception as e:
        print(f'Cannot reach Caddy on {CADDY_HOST}:{CADDY_PORT}: {e}')
        client_w.close()
        return
    await asyncio.gather(pipe(client_r, upstream_w), pipe(upstream_r, client_w))

async def main():
    server = await asyncio.start_server(handle, '0.0.0.0', LISTEN_PORT)
    print(f'TCP proxy listening on 0.0.0.0:{LISTEN_PORT} -> {CADDY_HOST}:{CADDY_PORT}')
    async with server:
        await server.serve_forever()

if __name__ == '__main__':
    asyncio.run(main())
