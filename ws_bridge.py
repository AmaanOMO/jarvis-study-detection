import asyncio
import json
import threading
import websockets
from typing import Callable, Set, Optional
from websockets.server import WebSocketServerProtocol

class WebSocketBridge:
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.click_handler: Optional[Callable[[], None]] = None
        self.server: Optional[websockets.WebSocketServer] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        
    async def register_client(self, websocket: WebSocketServerProtocol):
        """Register a new client connection."""
        self.clients.add(websocket)
        print(f"🌐 Client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send initial status
            await websocket.send(json.dumps({
                "type": "connected",
                "message": "Connected to Jarvis HUD"
            }))
            
            # Keep connection alive and handle messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    print(f"❌ Invalid JSON received: {message}")
                except Exception as e:
                    print(f"❌ Error handling message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self.clients.discard(websocket)
            print(f"🌐 Client disconnected. Total clients: {len(self.clients)}")
    
    async def _handle_message(self, websocket: WebSocketServerProtocol, data: dict):
        """Handle incoming messages from clients."""
        msg_type = data.get("type")
        
        if msg_type == "click":
            print("🎯 Orb clicked in browser!")
            if self.click_handler:
                # Call the handler in the main thread
                threading.Thread(target=self.click_handler, daemon=True).start()
        elif msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong"}))
        else:
            print(f"📨 Unknown message type: {msg_type}")
    
    async def broadcast(self, payload: dict):
        """Broadcast a message to all connected clients."""
        if not self.clients:
            return
            
        message = json.dumps(payload)
        disconnected_clients = set()
        
        for client in self.clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                print(f"❌ Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        # Remove disconnected clients
        self.clients -= disconnected_clients
    
    def on_click(self, handler: Callable[[], None]):
        """Set the callback for when the orb is clicked in the browser."""
        self.click_handler = handler
        print("🎯 Click handler registered")
    
    async def start_server(self):
        """Start the WebSocket server."""
        self.server = await websockets.serve(
            self.register_client,
            self.host,
            self.port
        )
        print(f"🌐 WebSocket server started on ws://{self.host}:{self.port}")
        
        # Keep the server running
        await self.server.wait_closed()
    
    def start_ws_server_in_thread(self):
        """Start the WebSocket server in a background thread."""
        def run_server():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.start_server())
        
        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        print("🌐 WebSocket server starting in background thread...")
        
        # Wait a moment for server to start
        import time
        time.sleep(0.5)
    
    def broadcast_sync(self, payload: dict):
        """Synchronous wrapper for broadcast (for use in main thread)."""
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.broadcast(payload), 
                self.loop
            )

# Global instance
ws_bridge = WebSocketBridge()

# Convenience functions
def start_ws_server_in_thread():
    """Start the WebSocket server in a background thread."""
    ws_bridge.start_ws_server_in_thread()

def broadcast(payload: dict):
    """Broadcast a message to all connected clients."""
    ws_bridge.broadcast_sync(payload)

def on_click(handler: Callable[[], None]):
    """Set the callback for when the orb is clicked in the browser."""
    ws_bridge.on_click(handler)

if __name__ == "__main__":
    # Test the server
    print("🧪 Testing WebSocket bridge...")
    start_ws_server_in_thread()
    
    # Keep main thread alive
    try:
        while True:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
