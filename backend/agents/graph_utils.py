from __future__ import annotations

import contextvars
import logging
import time
from concurrent.futures import TimeoutError, ThreadPoolExecutor
from typing import Callable, TypeVar

from config import settings
from sqlalchemy.orm import Session

logger = logging.getLogger("graph_utils")

StateT = TypeVar("StateT", bound=dict)

_NODE_TIMEOUT = max(getattr(settings, "node_timeout_seconds", 60), 10)


def create_db_context():
    _db_context: contextvars.ContextVar[Session | None] = contextvars.ContextVar("db", default=None)

    def set_db(db: Session | None) -> None:
        _db_context.set(db)

    def _get_db() -> Session | None:
        return _db_context.get()

    return set_db, _get_db


def _make_step(name: str, inp: str, out: str, status: str, start: float) -> dict:
    duration = int((time.time() - start) * 1000)
    logger.info("[%s] %s | %s → %s (%dms)", status, name, inp[:60], out[:60], duration)
    return {
        "name": name,
        "input_summary": inp,
        "output_summary": out,
        "duration_ms": duration,
        "status": status,
    }


def _safe_node(node_fn: Callable[[StateT], dict], raise_on: tuple = ()):
    def wrapper(state: StateT) -> dict:
        start = time.time()
        try:
            updates = node_fn(state)
            # LangGraph 0.3 + StateGraph(dict) 行为：节点返回的 dict 不会自动 merge 到 state
            # 改用 {**state, **updates} 返回完整 state，确保后续节点能拿到所有累积字段
            if isinstance(updates, dict):
                return {**(state if isinstance(state, dict) else {}), **updates}
            return state if isinstance(state, dict) else {}
        except raise_on:
            raise
        except Exception as e:
            err = str(e)
            logger.error("[failed] %s: %s", node_fn.__name__, err)
            step = _make_step(node_fn.__name__, "", f"error: {err}", "failed", start)
            base = state if isinstance(state, dict) else {}
            return {
                **base,
                "agent_steps": base.get("agent_steps", []) + [step],
                "llm_used": base.get("llm_used", False),
                "llm_error": base.get("llm_error", "") or err,
            }

    wrapper.__name__ = node_fn.__name__
    return wrapper


def _with_timeout(node_fn: Callable[[StateT], dict], timeout: int = _NODE_TIMEOUT):
    def wrapper(state: StateT) -> dict:
        start = time.time()
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(node_fn, state)
            try:
                return future.result(timeout=timeout)
            except TimeoutError:
                pool.shutdown(wait=False)
                err = f"node timed out after {timeout}s"
                logger.error("[timeout] %s: %s", node_fn.__name__, err)
                step = _make_step(node_fn.__name__, "", f"error: {err}", "failed", start)
                return {
                    "agent_steps": state.get("agent_steps", []) + [step],
                    "llm_used": False,
                    "llm_error": state.get("llm_error", "") or err,
                }

    wrapper.__name__ = node_fn.__name__
    return wrapper
