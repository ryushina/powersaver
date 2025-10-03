import serial

class SMSSender:
    def __init__(self, port="COM11", baud=115200, number=None, message=None):
        self.port = port
        self.baud = baud
        self.number = self.e164(number) if number else None
        self.message = message

    def e164(self, ph: str) -> str:
        """Normalize PH number into E.164 (+63) format"""
        if not ph:
            return None
        ph = ph.strip().replace(" ", "").replace("-", "")
        if ph.startswith("+"): return ph
        if ph.startswith("0"): return "+63" + ph[1:]
        if ph.startswith("63"): return "+" + ph
        return ph

    def set_number(self, number: str):
        """Change destination number"""
        self.number = self.e164(number)

    def set_message(self, message: str):
        """Change message text"""
        self.message = message

    def send(self):
        """Fire-and-forget send (no waiting for modem response)"""
        if not self.number or not self.message:
            raise ValueError("Both number and message must be set before sending.")

        with serial.Serial(self.port, self.baud, timeout=1, write_timeout=5) as ser:
            # minimal setup
            ser.write(b"AT\r")
            ser.write(b"AT+CMGF=1\r")        # text mode
            ser.write(b'AT+CSCS="GSM"\r')    # charset

            # send SMS command
            ser.write(f'AT+CMGS="{self.number}"\r'.encode("ascii", "ignore"))
            ser.write(self.message.encode("ascii", "ignore") + b"\x1A")
            ser.flush()

        print(f"📨 SMS to {self.number} pushed to modem (fire & forget).")

# Example usage
if __name__ == "__main__":
    sms = SMSSender(port="COM11", baud=115200,
                    number="09533000636",
                    message="Hello from class-based fire & forget!")
    sms.send()
