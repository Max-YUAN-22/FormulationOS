"""FormulationOS: A Scientific Operating System for Computational Pharmaceutics."""

try:
    from importlib.metadata import PackageNotFoundError, version

    try:
        __version__ = version("formulation-os")
    except PackageNotFoundError:  # pragma: no cover - source checkout, not installed
        __version__ = "0.1.0.dev0"
except Exception:  # pragma: no cover - defensive
    __version__ = "0.1.0.dev0"