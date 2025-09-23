import asyncio
from tapo import ApiClient

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
        self._connected = False

    async def connect(self):
        """
        Connect to the Tapo P105 plug.
        """
        print(f"[DEBUG] Connecting to Tapo P105 at {self.plug_ip}...")
        self.plug = await self.client.p105(self.plug_ip)
        self._connected = True
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

    async def turn_off(self):
        """
        Turn the plug OFF.
        """
        if not self.plug:
            raise RuntimeError("Plug is not connected. Call connect() first.")
        print("Turning OFF the plug...")
        await self.plug.off()

    async def cycle_power(self, delay: int = 5):
        """
        Turn the plug ON, wait for a given delay, then turn it OFF.
        """
        await self.turn_on()
        print(f"[DEBUG] Waiting {delay} seconds before turning off...")
        await asyncio.sleep(delay)
        await self.turn_off()

    async def get_state(self) -> bool:
        """
        Get the current state of the plug.

        Returns:
            bool: True if the plug is ON, False if OFF.
        """
        if not self.plug:
            raise RuntimeError("Plug is not connected. Call connect() first.")

        state = await self.plug.get_state()

        # Debug: print raw state
        print(f"[DEBUG] Raw state data: {state}")

        # The 'on' key in the returned dict tells us if it's powered
        is_on = state.get("on", False)
        status = "ON" if is_on else "OFF"
        print(f"[DEBUG] Plug is currently {status}")

        return is_on
    
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
        
        return loop.run_until_complete(self.get_state())