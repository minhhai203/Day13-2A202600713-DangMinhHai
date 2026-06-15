"""Runtime shim for bundled pydantic_core on private/public simulators."""
from __future__ import annotations

import glob
import importlib.machinery
import importlib.util
import os
import sys
from pkgutil import extend_path

__path__ = extend_path(__path__, __name__)  # type: ignore[name-defined]

try:
    from typing_extensions import Sentinel
except Exception:  # pragma: no cover - fallback for stripped runtimes
    Sentinel = None  # type: ignore[assignment]


def _runtime_root() -> str | None:
    here = os.path.abspath(os.path.dirname(__file__))
    roots = [
        os.path.join(here, ".runtime"),
        os.path.join(here, "..", ".runtime"),
    ]
    for base in roots:
        pattern = os.path.join(os.path.abspath(base), "observathon-*", "pydantic_core", "_pydantic_core*.so")
        matches = sorted(glob.glob(pattern))
        if matches:
            return os.path.dirname(matches[0])
    return None


def _load_ext() -> None:
    modname = f"{__name__}._pydantic_core"
    if modname in sys.modules:
        return
    root = _runtime_root()
    if not root:
        return
    candidates = sorted(glob.glob(os.path.join(root, "_pydantic_core*.so")))
    if not candidates:
        return
    so_path = candidates[0]
    spec = importlib.util.spec_from_file_location(modname, so_path)
    if not spec or not isinstance(spec.loader, importlib.machinery.ExtensionFileLoader):
        return
    module = importlib.util.module_from_spec(spec)
    sys.modules[modname] = module
    spec.loader.exec_module(module)
    if hasattr(module, "__version__"):
        globals()["__version__"] = getattr(module, "__version__")
    globals().update({name: getattr(module, name) for name in dir(module) if not name.startswith("_")})


_load_ext()

try:
    from . import core_schema as core_schema  # noqa: F401
    from .core_schema import CoreConfig, CoreSchema, CoreSchemaType, ErrorType  # noqa: F401
except Exception:
    core_schema = None  # type: ignore[assignment]

if "PydanticUndefined" in globals():
    UNSET = globals()["PydanticUndefined"]
else:  # pragma: no cover - only for severely stripped runtimes
    UNSET = object()

if Sentinel is not None:
    MISSING = Sentinel("MISSING")
else:  # pragma: no cover - only for severely stripped runtimes
    MISSING = object()
