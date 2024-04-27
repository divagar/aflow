import asyncio
import logging
from ws4py.server.tulipserver import WebSocketProtocol
from ws4py.websocket import WebSocket

logging.basicConfig(level=logging.INFO)


class MyWebSocket(WebSocket):
    async def received_message(self, message):
        # Echo the message back to the client
        await self.send(message.data, message.is_binary)


async def websocketHandler(request):
    ws = MyWebSocket(WebSocketProtocol)
    await ws.prepare(request)
    return ws


async def main():
    server = await asyncio.start_server(
        protocol_factory=lambda: WebSocketProtocol(websocketHandler),
        host='127.0.0.1',
        port=8765,
    )

    logging.info("Server started at ws://127.0.0.1:8765")

    async with server:
        try:
            await server.serve_forever()
        except asyncio.CancelledError:
            server.close()
            await server.wait_closed()

# Run the server
try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.info("Server stopped manually.")
except Exception as e:
    logging.error(f"Server error: {e}")
