import asyncio
from tapo_controller import TapoPlugController
from diskcache import Cache
import time
from sms_sender import SMSSender
from infra_sqlite import SQLiteLogRepo
from datetime import datetime

KEY = "person_count"
people=[]

async def main():
    logger = SQLiteLogRepo()
    turn_on_mes = SMSSender(number="09533000636",message="Successfully turned on device")
    turn_off_mes = SMSSender(number="09533000636",message="Devices are turned off")
    controller = TapoPlugController(
        "rustanlacanilao@gmail.com",
        "iTpower@123",
        "192.168.0.128"
    )
    await controller.connect()
    await controller.turn_off()


    with Cache("./app_cache") as cache:
        try:
            while True:
                val = int(cache.get(KEY,0))
                people.append(val)
                now = datetime.now()
                await logger.log(now.strftime("%Y-%m-%d %H:%M:%S"), str(val),cache.get("is_tapo_on"))
                if len(people) == 30:
                    del people[0]
                    if all(v == 0 for v in people ) and bool(cache.get("is_tapo_on"))  == True:
                        await controller.turn_off()
                        turn_off_mes.send()
                print(f"[{time.strftime('%H:%M:%S')}] {KEY} = {val!r} {cache.get("is_tapo_on")}")
                if bool(cache.get("is_tapo_on"))==False and val>0:
                    await controller.turn_on()
                    turn_on_mes.send()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopped.")





try:
    asyncio.run(main())
except Exception as exc:
    print(f"[DEBUG] Exception in main: {exc}")
    import traceback
    traceback.print_exc()