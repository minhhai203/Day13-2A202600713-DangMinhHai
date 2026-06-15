"""Compatibility shim for runtimes missing stdlib `shlex`."""
from __future__ import annotations

import importlib.util
import os

_stdlib_dir = os.path.dirname(os.__file__)
_stdlib_file = os.path.join(_stdlib_dir, "shlex.py")

if os.path.exists(_stdlib_file):
    _spec = importlib.util.spec_from_file_location("_stdlib_shlex", _stdlib_file)
    if _spec and _spec.loader:
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        for _name, _value in _mod.__dict__.items():
            if _name in {"__name__", "__loader__", "__package__", "__spec__"}:
                continue
            globals()[_name] = _value
        __all__ = getattr(_mod, "__all__", [n for n in globals() if not n.startswith("_")])
    else:
        raise ImportError("unable to load stdlib shlex")
else:
    raise ImportError("stdlib shlex.py not found")
