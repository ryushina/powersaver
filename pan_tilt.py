import time
from amcrest import AmcrestCamera

# ====== CONFIGURATION ======
IP = "192.168.0.184"
PORT = 80
USERNAME = "admin"
PASSWORD = "iTpower@123"
SPEED = 1         # 1 = slowest, 8 = fastest
DURATION = 5      # seconds to pan in one direction
# ===========================

cam = AmcrestCamera(IP, PORT, USERNAME, PASSWORD).camera

def pan_once(direction, speed=SPEED, duration=DURATION):
    """
    Move camera in the specified direction for a given duration, then stop.
    direction: 'Left' or 'Right'
    """
    print(f"[INFO] Panning {direction} at speed {speed} for {duration} seconds...")
    cam.ptz_control_command("start", code=direction, arg2=speed)
    time.sleep(duration)
    cam.ptz_control_command("stop", code=direction)
    print(f"[INFO] Stopped {direction} movement.")

def sweep_forever():
    """
    Continuously pan left and right.
    Press CTRL + C to stop the script.
    """
    print("[INFO] Starting infinite left-right sweep. Press CTRL+C to exit.")
    while True:
        pan_once("Left")
        time.sleep(1)  # pause before switching direction
        pan_once("Right")
        time.sleep(1)

def main():
    try:
        sweep_forever()
    except KeyboardInterrupt:
        print("\n[INFO] Stopped by user. Exiting gracefully...")
    except Exception as e:
        print(f"[DEBUG] Exception in main: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
