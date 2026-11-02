import os


def env_int(name: str, default: int, min_value: int, max_value: int) -> int:
    try:
        value = int(os.environ.get(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(min_value, min(max_value, value))
