import serial

PORT = "COM11"
BAUD = 115200
TARGET = "09533000636"
MESSAGE = "Hello from Python – pure fire & forget!"

def e164(ph):
    ph = ph.strip().replace(" ", "").replace("-", "")
    if ph.startswith("+"): return ph
    if ph.startswith("0"): return "+63" + ph[1:]
    if ph.startswith("63"): return "+" + ph
    return ph

def send_sms():
    dest = e164(TARGET)
    with serial.Serial(PORT, BAUD, timeout=1, write_timeout=5) as ser:
        # minimal setup (no waiting for replies)
        ser.write(b"AT\r")
        ser.write(b"AT+CMGF=1\r")        # text mode
        ser.write(b'AT+CSCS="GSM"\r')    # charset

        # send SMS command
        ser.write(f'AT+CMGS="{dest}"\r'.encode("ascii", "ignore"))
        # directly push body + Ctrl+Z
        ser.write(MESSAGE.encode("ascii", "ignore") + b"\x1A")
        ser.flush()

    print("📨 Message pushed to modem (no wait, no prompt).")

if __name__ == "__main__":
    send_sms()
