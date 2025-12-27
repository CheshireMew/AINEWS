try:
    import zoneinfo
    print("zoneinfo imported")
    try:
        tz = zoneinfo.ZoneInfo("Asia/Shanghai")
        print(f"Success: {tz}")
    except Exception as e:
        print(f"Failed to load Asia/Shanghai: {e}")
except ImportError:
    print("zoneinfo not found")

import importlib.util
spec = importlib.util.find_spec("tzdata")
print(f"tzdata installed: {spec is not None}")
