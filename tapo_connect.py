import asyncio
from tapo import ApiClient


async def main():
    # Replace with your Tapo account email and password
    username = "rustanlacanilao@gmail.com"
    password = "iTpower@123"

    # Local IP of your P105 plug
    plug_ip = "192.168.0.128"

    # Initialize Tapo client
    client = ApiClient(username, password)

    # Connect to your P105 device
    plug = await client.p105(plug_ip)

    # Turn it ON
    print("Turning ON the plug...")
    await plug.on()

    # Wait 5 seconds
    await asyncio.sleep(5)

    # Turn it OFF
    print("Turning OFF the plug...")
    await plug.off()


if __name__ == "__main__":
    asyncio.run(main())
