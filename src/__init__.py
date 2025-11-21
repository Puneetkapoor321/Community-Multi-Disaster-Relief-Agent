"""
CommunityRelief agents src package bootstrap.

The file ensures Python treats `src` as a package so that the existing
relative imports (e.g. `from .agents import ...`) continue to work even
when modules are executed via `python -m src.<module>`.
"""

__all__ = []
