import time


NETWORK_REQUEST_GAP_MS = 10 * 1000


_state = {
    "active": False,
    "owner": None,
    "next_allowed_ms": None,
    "last_owner": None,
    "last_release_ms": None,
}


def initialize(now_ms=None):
    if now_ms is None:
        now_ms = time.ticks_ms()
    _state["active"] = False
    _state["owner"] = None
    _state["next_allowed_ms"] = now_ms
    _state["last_owner"] = None
    _state["last_release_ms"] = None


def try_acquire(owner, now_ms):
    if _state["active"]:
        return False

    next_allowed_ms = _state["next_allowed_ms"]
    if next_allowed_ms is not None and time.ticks_diff(now_ms, next_allowed_ms) < 0:
        return False

    _state["active"] = True
    _state["owner"] = owner
    return True


def release(owner, now_ms):
    if not _state["active"] or _state["owner"] != owner:
        return False

    _state["active"] = False
    _state["owner"] = None
    _state["last_owner"] = owner
    _state["last_release_ms"] = now_ms
    _state["next_allowed_ms"] = time.ticks_add(now_ms, NETWORK_REQUEST_GAP_MS)
    return True


def get_state():
    return {
        "active": _state["active"],
        "owner": _state["owner"],
        "next_allowed_ms": _state["next_allowed_ms"],
        "last_owner": _state["last_owner"],
        "last_release_ms": _state["last_release_ms"],
    }


def get_last_release_ms(owner):
    if _state["last_owner"] != owner:
        return None
    return _state["last_release_ms"]
