import json
import os
from datetime import datetime
from config.settings import Config

class TrialManager:
    def __init__(self):
        self.trials_file = Config.TRIALS_FILE
        self.rules_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'trial_rules.json')
        self.ensure_file()

    def load_rules(self):
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"max_batches": 10, "max_files": 30}

    def ensure_file(self):
        if not os.path.exists(self.trials_file):
            os.makedirs(os.path.dirname(self.trials_file), exist_ok=True)
            with open(self.trials_file, 'w') as f:
                json.dump({}, f)

    def load_trials(self):
        try:
            with open(self.trials_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_trials(self, trials):
        with open(self.trials_file, 'w') as f:
            json.dump(trials, f, indent=2)

    def check_trial(self, hardware_id):
        trials = self.load_trials()
        rules = self.load_rules()
        max_files = rules.get("max_files", 30)
        
        if hardware_id not in trials:
            return {
                "allowed": True, 
                "remaining_files": max_files,
                "files_used": 0
            }
        
        data = trials[hardware_id]
        files_used = data.get("files_used", 0)
        
        allowed = files_used < max_files
        
        return {
            "allowed": allowed,
            "remaining_files": max(0, max_files - files_used),
            "files_used": files_used,
            "limits": {"files": max_files}
        }

    def increment_trial(self, hardware_id, files_count=1):
        trials = self.load_trials()
        rules = self.load_rules()
        max_files = rules.get("max_files", 30)
        now = datetime.utcnow().isoformat()
        
        if hardware_id not in trials:
            trials[hardware_id] = {
                "files_used": 0,
                "first_seen": now,
                "last_seen": now
            }
            
        data = trials[hardware_id]
        # Migrate legacy data if needed
        if "conversions_used" in data:
            # Legacy users might have used batches, but we only care about files now.
            # We can either reset them or try to estimate. Let's reset to be safe/generous.
            if "files_used" not in data:
                data["files_used"] = 0
            del data["conversions_used"]
            
        data["last_seen"] = now
        
        if data["files_used"] < max_files:
            data["files_used"] = data.get("files_used", 0) + files_count
            self.save_trials(trials)
            
            return {
                "success": True, 
                "files_used": data["files_used"],
                "remaining_files": max(0, max_files - data["files_used"])
            }
        else:
            return {
                "success": False,
                "message": "Trial limit reached",
                "files_used": data.get("files_used", 0),
                "remaining_files": 0
            }

    def reset_trial(self, hardware_id):
        trials = self.load_trials()
        if hardware_id in trials:
            trials[hardware_id]["batches_used"] = 0
            trials[hardware_id]["files_used"] = 0
            if "conversions_used" in trials[hardware_id]:
                del trials[hardware_id]["conversions_used"]
            self.save_trials(trials)
            return {"success": True, "message": "Trial reset"}
        return {"success": False, "message": "Hardware ID not found"}
