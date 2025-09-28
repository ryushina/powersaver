import asyncio

from sympy import false
from tapo import ApiClient
import inspect

class TapoPlugController:
    def __init__(self, username: str, password: str, plug_ip: str):
        """
        Initialize the TapoPlugController with Tapo account credentials and device IP.
        """
        self.username = username
        self.password = password
        self.plug_ip = plug_ip
        self.client = ApiClient(username, password)
        self.plug = None
        self.connected = False
        self.is_tapo_on = False

    async def connect(self):
        """
        Connect to the Tapo P105 plug.
        """
        print(f"[DEBUG] Connecting to Tapo P105 at {self.plug_ip}...")
        self.plug = await self.client.p105(self.plug_ip)
        self.connected = True
        print("[DEBUG] Connected successfully!")
    
    def connect_sync(self):
        """
        Synchronous wrapper for connect() method.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.connect())

    async def turn_on(self):
        """
        Turn the plug ON.
        """
        if not self.plug:
            raise RuntimeError("Plug is not connected. Call connect() first.")
        print("Turning ON the plug...")
        await self.plug.on()
        self.is_tapo_on = True

    async def turn_off(self):
        """
        Turn the plug OFF.
        """
        if not self.plug:
            raise RuntimeError("Plug is not connected. Call connect() first.")
        print("Turning OFF the plug...")
        await self.plug.off()
        self.is_tapo_on = False

    async def cycle_power(self, delay: int = 5):
        """
        Turn the plug ON, wait for a given delay, then turn it OFF.
        """
        await self.turn_on()
        print(f"[DEBUG] Waiting {delay} seconds before turning off...")
        await asyncio.sleep(delay)
        await self.turn_off()

    @property
    async def get_state(self) -> bool:
        if not self.plug:
            raise RuntimeError("Plug is not connected. Call connect() first.")
            # Prefer a direct boolean if available
        if hasattr(self.plug, "is_on"):
            fn = self.plug.is_on
            return await fn() if inspect.iscoroutinefunction(fn) else bool(fn())
        return False

    def get_state_sync(self) -> bool:
        """
        Synchronous wrapper for get_state() method.
        """
        if not self._connected:
            print("[DEBUG] Not connected, returning False")
            return False
            
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.get_state)