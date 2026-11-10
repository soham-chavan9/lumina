import json
import os
import time
from datetime import datetime
from functools import wraps
from backend.storage import data_dir

LOG_DIR = str(data_dir() / "logs")
LOG_FILE = os.path.join(LOG_DIR, "performance_log.jsonl")

os.makedirs(LOG_DIR, exist_ok=True)

def log_performance(func):
    """Decorator to log API function execution time."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = round(time.time() - start, 3)

        log_entry = {
            "function": func.__name__,
            "timestamp": datetime.now().isoformat(),
            "duration_s": duration
        }

        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

        print(f"⚡ {func.__name__} took {duration}s")
        return result
    return wrapper
