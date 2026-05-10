import time
import os

class CleanManager:

    def __init__(self, paths, cooldown_minutes=20):
        self.paths = paths
        self.cooldown = cooldown_minutes * 60  # segundos
        self.state_file = os.path.join(self.paths.CFG_DIR, "cfg_3.json")
        state = self.paths.manage_json(filepath=self.state_file, mode="read", default={"last_clean": 0})
        if "last_clean" not in state:
            self.paths.manage_json(filepath=self.state_file, mode="write", data={"last_clean": 0})

    def should_clean(self):
        state = self.paths.manage_json(self.state_file, "read", default={"last_clean": 0})
        last_t = state.get("last_clean", 0)
        now = time.time()
        if last_t == 0:
            self._update_timestamp()
            return True
        if now - last_t >= self.cooldown:
            self._update_timestamp()
            return True
        return False

    def _update_timestamp(self):
        self.paths.manage_json(self.state_file, "write",{"last_clean": time.time()})
