import re
import time
import serial
from typing import Optional, Dict, Any


class SMSSender:
    def __init__(self, port="COM11", baud=115200, number: Optional[str] = None, message: Optional[str] = None):
        self.port = port
        self.baud = baud
        self.number = self.e164(number) if number else None
        self.message = message

    # ---------- low-level serial ----------
    def _open(self):
        # timeout is read-timeout; write_timeout prevents long blocking writes
        return serial.Serial(self.port, self.baud, timeout=1, write_timeout=5)

    def _read_until(self, ser, token: Optional[str] = None, timeout: float = 20.0) -> str:
        """Read bytes until token appears or timeout; returns accumulated buffer."""
        end = time.time() + timeout
        buf = ""
        while time.time() < end:
            chunk = ser.read(ser.in_waiting or 1).decode(errors="ignore")
            if chunk:
                buf += chunk
                if token and token in buf:
                    break
            else:
                time.sleep(0.05)
        return buf

    @staticmethod
    def _extract_last_cusd(buf: str) -> Optional[str]:
        """Return the last '+CUSD:' line from a modem buffer (raw)."""
        lines = [ln for ln in buf.splitlines() if "+CUSD:" in ln]
        return lines[-1] if lines else None

    # ---------- utils ----------
    def e164(self, ph: str) -> Optional[str]:
        """Normalize PH number into E.164 (+63...) format."""
        if not ph:
            return None
        ph = ph.strip().replace(" ", "").replace("-", "")
        if ph.startswith("+"):
            return ph
        if ph.startswith("0"):
            return "+63" + ph[1:]
        if ph.startswith("63"):
            return "+" + ph
        return ph

    @staticmethod
    def _decode_cusd(payload: str, dcs: Optional[int]) -> str:
        """
        Robust decode for +CUSD payloads.
        - Strips outer/stray quotes
        - Removes non-hex chars when detecting UCS2 hex (Smart common)
        - Decodes as UTF-16BE when DCS=8/72 or payload looks like hex
        """
        raw = payload.strip()
        if raw.startswith('"') and raw.endswith('"'):
            raw = raw[1:-1]
        else:
            raw = raw.replace('"', '')

        # best-effort DCS parse
        try:
            dcs_int = int(dcs) if dcs is not None else None
        except Exception:
            dcs_int = None

        # if hex-like, keep only hex chars to tolerate partial quotes/spaces
        hex_only = re.sub(r'[^0-9A-Fa-f]', '', raw)
        looks_hex = len(hex_only) > 0 and len(hex_only) % 2 == 0

        if dcs_int in (8, 72) or looks_hex:
            try:
                return bytes.fromhex(hex_only).decode("utf-16-be", errors="replace").strip()
            except Exception as e:
                return f"[decode error: {e}] {raw}"

        return raw.strip()

    # ---------- setters ----------
    def set_number(self, number: str):
        self.number = self.e164(number)

    def set_message(self, message: str):
        self.message = message

    # ---------- SMS: fire & forget ----------
    def send(self):
        """Fire-and-forget send (no waiting for modem response)."""
        if not self.number or not self.message:
            raise ValueError("Both number and message must be set before sending.")

        with self._open() as ser:
            ser.write(b"AT\r")
            ser.write(b"AT+CMGF=1\r")          # text mode
            ser.write(b'AT+CSCS="GSM"\r')      # charset

            ser.write(f'AT+CMGS="{self.number}"\r'.encode("ascii", "ignore"))
            ser.write(self.message.encode("ascii", "ignore") + b"\x1A")
            ser.flush()

        print(f"📨 SMS to {self.number} pushed to modem (fire & forget).")

    # ---------- USSD ----------
    def send_ussd(self, code: str, timeout: int = 20, cancel: bool = True) -> str:
        """
        Send a USSD code (e.g., '*123#') or a session reply (e.g., '1') and return decoded text.
        Uses AT+CUSD; falls back to ATD*code#; if needed. Includes a short 'settle' read to capture full lines.
        """
        with self._open() as ser:
            ser.reset_input_buffer()
            ser.write(b"AT\r")
            self._read_until(ser, "OK", 2)

            # Send request (both initial and reply go via AT+CUSD=1,"...",15)
            cmd = f'AT+CUSD=1,"{code}",15\r'.encode("ascii")
            ser.write(cmd)

            # Wait until we see '+CUSD', then keep reading briefly so the full line arrives
            raw = self._read_until(ser, token="+CUSD", timeout=timeout)

            # settle window: keep grabbing trailing chunks
            end = time.time() + 1.0
            while time.time() < end:
                chunk = ser.read(ser.in_waiting or 1).decode(errors="ignore")
                if chunk:
                    raw += chunk
                    end = time.time() + 0.2  # extend if data continues
                else:
                    time.sleep(0.05)

            cusd = self._extract_last_cusd(raw)

            if not cusd and code.strip().startswith("*") and code.strip().endswith("#"):
                # Fallback: some modules prefer dial style
                ser.write(f"ATD{code};\r".encode("ascii"))
                raw2 = self._read_until(ser, token="+CUSD", timeout=timeout)
                # settle again
                end = time.time() + 1.0
                while time.time() < end:
                    chunk = ser.read(ser.in_waiting or 1).decode(errors="ignore")
                    if chunk:
                        raw2 += chunk
                        end = time.time() + 0.2
                    else:
                        time.sleep(0.05)
                cusd = self._extract_last_cusd(raw2)
                raw += "\n" + raw2

            if cusd:
                # +CUSD: <n>,"<payload>",<dcs>
                m = re.search(r'\+CUSD:\s*\d\s*,\s*(".*?"|[^,]+)\s*(?:,\s*([0-9]+))?', cusd)
                if m:
                    payload = m.group(1).strip()
                    dcs = m.group(2) if len(m.groups()) >= 2 else None
                    text = self._decode_cusd(payload, dcs)
                else:
                    text = cusd
            else:
                text = raw.strip()

            # End session gracefully unless the caller requests otherwise
            if cancel:
                try:
                    ser.write(b"AT+CUSD=2\r")
                    self._read_until(ser, "OK", 2)
                except Exception:
                    pass

            return text.strip()

    # ---------- Smart balance (auto-follow '1') ----------
    def check_balance(self, carrier: str = "smart", auto_follow: bool = True, timeout: int = 25) -> str:
        """
        For Smart/TNT/Sun:
          1) *123# to open menu
          2) If menu detected and auto_follow, reply '1' to fetch Balance + active promos.
        Returns final decoded text.
        """
        carrier = (carrier or "smart").lower()

        if carrier in ("smart", "tnt", "sun", "auto"):
            first = self.send_ussd("*123#", timeout=timeout, cancel=False)

            if not auto_follow:
                # close and return first screen
                try:
                    with self._open() as ser:
                        ser.write(b"AT+CUSD=2\r")
                        self._read_until(ser, "OK", 2)
                except Exception:
                    pass
                return first

            # Detect typical menu (option 1 is Balance)
            looks_menu = bool(re.search(r"\b1[\).:\-]\s*(Balance|Bal)\b", first, re.IGNORECASE)) \
                         or (re.search(r"\bBalance\b", first, re.IGNORECASE) and re.search(r"\b1[\).:\-]\b", first))

            if looks_menu:
                # follow with '1' to get balance/promos
                details = self.send_ussd("1", timeout=timeout, cancel=True)
                return details if details else first

            # sometimes balance is already shown on first screen
            try:
                with self._open() as ser:
                    ser.write(b"AT+CUSD=2\r")
                    self._read_until(ser, "OK", 2)
            except Exception:
                pass
            return first

        # Other carriers quick default
        code = "*143#" if carrier in ("globe", "tm") else "*121#" if carrier == "dito" else "*123#"
        return self.send_ussd(code, timeout=timeout, cancel=True)

    # ---------- optional: quick parser ----------
    @staticmethod
    def parse_balance_and_promos(text: str) -> Dict[str, Any]:
        """Best-effort parse of peso balance, data, validity, and promo lines."""
        out: Dict[str, Any] = {"raw": text}

        m = re.search(r'(?:Php?|₱)\s*([0-9]+(?:\.[0-9]{1,2})?)', text, re.IGNORECASE)
        if m:
            out["peso_balance"] = float(m.group(1))

        m = re.search(r'([0-9]+(?:\.[0-9]+)?)\s*(GB|MB)\b', text, re.IGNORECASE)
        if m:
            out["data_balance"] = f"{m.group(1)} {m.group(2).upper()}"

        m = re.search(r'(?:valid (?:until|up to)\s*)([A-Za-z0-9/\- :]+)', text, re.IGNORECASE)
        if m:
            out["validity"] = m.group(1).strip()

        promos = []
        for line in text.splitlines():
            if re.search(r'(registered to|promo|giga|unli|allnet)', line, re.IGNORECASE):
                promos.append(line.strip())
        if promos:
            out["promos"] = promos

        return out


# ---------- example usage ----------
if __name__ == "__main__":
    sms = SMSSender(
        port="COM11",
        baud=115200,
        number="09533000636",
        message="Hello from class-based fire & forget!"
    )

    # Fire-and-forget SMS
    # sms.send()

    # Smart balance + promos (auto replies "1" after *123#)
    txt = sms.check_balance(carrier="smart", auto_follow=True)
    print("💳 Balance/USSD reply:\n", txt)

    # Optional structured parse
    parsed = SMSSender.parse_balance_and_promos(txt)
    print("\nParsed:", parsed)
