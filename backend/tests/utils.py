from __future__ import annotations

import functools
import inspect
from types import SimpleNamespace
from typing import Any, Sequence
from unittest.mock import MagicMock, patch


class Patches(SimpleNamespace):
    """
    Holds started mocks as attributes (e.g., mock_foo) and also in .by_name (key w/o 'mock_').
    """

    by_name: dict[str, MagicMock]


def patches(targets: Sequence[str], *, autospec: bool = True):
    """
    Decorator that applies multiple patch()es and passes a Patches context
    as an extra arg to the test function.

    Usage:
        @patches(["api.views.serialize_and_save_photograph", "api.views.validate_photograph"])
        def test_something(self, p: Patches):
            p.mock_validate_photograph.assert_called_once()
            p.mock_serialize_and_save_photograph.assert_not_called()
    """

    def decorator(fn):
        is_async = inspect.iscoroutinefunction(fn)

        def _start_all() -> tuple[list[Any], Patches]:
            patchers: list[Any] = []
            attrs: dict[str, MagicMock] = {}
            plain: dict[str, MagicMock] = {}
            for target in targets:
                name = target.rsplit(".", 1)[-1]
                attr = f"mock_{name}"
                # avoid accidental collisions (rare, but safe)
                i = 2
                original_attr = attr
                while attr in attrs:
                    attr = f"{original_attr}_{i}"
                    i += 1

                p = patch(target, autospec=autospec)
                m: MagicMock = p.start()
                patchers.append(p)
                attrs[attr] = m
                plain[name] = m

            ctx = Patches(**attrs)
            # set .by_name after creation so type checkers are happy
            object.__setattr__(ctx, "by_name", plain)
            return patchers, ctx

        @functools.wraps(fn)
        def sync_wrapper(*args, **kwargs):
            patchers, ctx = _start_all()
            try:
                # inject ctx as next positional arg (after self, typically)
                return fn(*args, ctx, **kwargs)
            finally:
                for p in reversed(patchers):
                    p.stop()

        @functools.wraps(fn)
        async def async_wrapper(*args, **kwargs):
            patchers, ctx = _start_all()
            try:
                return await fn(*args, ctx, **kwargs)
            finally:
                for p in reversed(patchers):
                    p.stop()

        return async_wrapper if is_async else sync_wrapper

    return decorator
