class SharedState:
    def __init__(self):
        self.current_count = 0
        self.is_tapo_on = None
        self.last_nonzero_ts = 0

    def set_count(self, n):
        self.current_count = max(0, int(n))
        if n > 0:
            import time
            self.last_nonzero_ts = time.monotonic()

    def set_tapo_state(self, is_on):
        self.is_tapo_on = is_on

    def get_snapshot(self):
        return {
            "current_count": self.current_count,
            "is_tapo_on": self.is_tapo_on,
            "last_nonzero_ts": self.last_nonzero_ts,
        }
