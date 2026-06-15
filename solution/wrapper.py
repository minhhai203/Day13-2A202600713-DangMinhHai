"""Mitigation + observability layer for Observathon."""
from __future__ import annotations

import hashlib
import os
import re
import sys
import time
import traceback
import unicodedata
from copy import deepcopy

_vendor = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "vendor"))
if os.path.isdir(_vendor) and _vendor not in sys.path:
    sys.path.append(_vendor)

from telemetry.cost import cost_from_usage
from telemetry.logger import logger, new_correlation_id, set_correlation_id
from telemetry.redact import redact

_CATALOG = (
    ("airpods", "AirPods"),
    ("macbook", "MacBook"),
    ("iphone", "iPhone"),
    ("ipad", "iPad"),
    ("samsung", "Samsung"),
)
_INJECTION_PATTERNS = (
    re.compile(r"(?is)\b(?:ghi\s*ch[uú]|note)\s*:.*"),
    re.compile(r"(?is)\b(?:system|override|admin)\s*:.*"),
    re.compile(r"(?is)\b(?:ignore|b[oỏ]\s*qua)\s+(?:previous|system|rules?).*"),
    re.compile(r"(?is)\b(?:gia|price)\s*(?:he\s*thong|system|override)\s*(?:la|is|=).*(?:vnd|đ)?"),
)
_RETRYABLE = frozenset({"loop", "max_steps", "no_action", "wrapper_error"})
_TRANSIENT_TOOL_ERRORS = frozenset({"upstream_unavailable", "tool_error", "timeout"})
_NUMBER_WORDS = {
    "mot": 1,
    "một": 1,
    "hai": 2,
    "ba": 3,
    "bon": 4,
    "bốn": 4,
    "tu": 4,
    "tư": 4,
    "nam": 5,
    "năm": 5,
    "sau": 6,
    "sáu": 6,
    "bay": 7,
    "bảy": 7,
    "tam": 8,
    "tám": 8,
    "chin": 9,
    "chín": 9,
    "muoi": 10,
    "mười": 10,
}
_DELIVERY_INTENT = re.compile(
    r"\b(?:giao|ship(?:ped)?|delivery|gui|chuyen)\b",
    re.I,
)


class ParsedOrder:
    __slots__ = (
        "qty",
        "qty_confident",
        "product",
        "coupon",
        "destination",
        "delivery_requested",
        "asks_total",
        "asks_price",
    )

    def __init__(
        self,
        qty: int = 1,
        qty_confident: bool = True,
        product: str | None = None,
        coupon: str | None = None,
        destination: str | None = None,
        delivery_requested: bool = False,
        asks_total: bool = False,
        asks_price: bool = False,
    ):
        self.qty = qty
        self.qty_confident = qty_confident
        self.product = product
        self.coupon = coupon
        self.destination = destination
        self.delivery_requested = delivery_requested
        self.asks_total = asks_total
        self.asks_price = asks_price


class ComputedTotal:
    __slots__ = ("total", "product", "qty", "unit_price", "discount_pct", "shipping")

    def __init__(
        self,
        total: int,
        product: str,
        qty: int,
        unit_price: int,
        discount_pct: int,
        shipping: int,
    ):
        self.total = total
        self.product = product
        self.qty = qty
        self.unit_price = unit_price
        self.discount_pct = discount_pct
        self.shipping = shipping


def _normalize(text: str) -> str:
    if text is None:
        return ""
    return unicodedata.normalize("NFC", str(text).strip())


def _fold(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", _normalize(text).lower())
        if unicodedata.category(char) != "Mn"
    )


def _sanitize_question(question: str) -> str:
    q = _normalize(question)
    for pat in _INJECTION_PATTERNS:
        q = pat.sub("", q)
    return re.sub(r"\s{2,}", " ", q).strip()


def _parse_order(question: str) -> ParsedOrder:
    q = _sanitize_question(question)
    low = _fold(q)
    qty = 1
    qty_confident = True
    m = re.search(r"\b(?:mua|dat|lay|can|cho\s+toi)\s+(\d+)\b", low)
    if not m:
        m = re.search(r"\b(\d+)\s*(?:chiec|cai)?\s*(?:airpods|macbook|iphone|ipad|samsung)\b", low)
    if not m:
        m = re.search(r"\b(?:so\s+luong|qty)\s*[:=]?\s*(\d+)\b", low)
    if not m:
        m = re.search(r"\b(?:airpods|macbooks?|iphones?|ipads?|samsung)\s*(?:x|so\s+luong)\s*(\d+)\b", low)
    if m:
        qty = int(m.group(1))
        qty_confident = qty > 0
    else:
        words = "|".join(sorted((_fold(x) for x in _NUMBER_WORDS), key=len, reverse=True))
        m = re.search(
            rf"\b({words})\s+(?:(?:chiec|cai|cap)\s+)?(?:airpods|macbooks?|iphones?|ipads?|samsung)\b",
            low,
        )
        if m:
            qty = _NUMBER_WORDS.get(m.group(1), 1)
        elif re.search(r"\b(?:so\s+luong|qty|x)\b", low):
            qty_confident = False

    product = None
    for key, label in _CATALOG:
        if re.search(rf"\b{re.escape(key)}s?\b", low):
            product = label
            break
    if not product:
        m = re.search(r"\bcon\s+(airpods|macbook|iphone|ipad|samsung)\b", low)
        if m:
            product = dict(_CATALOG)[m.group(1)]

    coupon = None
    m = re.search(
        r"(?:dung\s+(?:ma|voucher|coupon)|ap\s+(?:dung\s+)?ma|"
        r"su\s+dung\s+(?:ma|voucher|coupon)|voi\s+(?:ma|voucher|coupon)|"
        r"ma|voucher|coupon)\s+([a-z0-9]+)",
        low,
        re.I,
    )
    if m:
        coupon = m.group(1).upper()

    destination = None
    delivery_requested = bool(_DELIVERY_INTENT.search(low))
    m = re.search(
        r"(?:giao|ship(?:ped)?|delivery|gui|chuyen)"
        r"(?:\s+(?:ve|den|toi|to))?\s+"
        r"(.+?)(?=\s*(?:,|;|-|\?|\.|$)|\s+(?:dung|ap|su\s+dung|voi)?\s*"
        r"(?:ma|voucher|coupon)\b|\s+(?:het|tong|tinh|bao\s+nhieu|cong|thanh\s+toan)\b)",
        low,
        re.I,
    )
    if m:
        destination = m.group(1).strip(" .,-")

    asks_total = bool(re.search(r"\b(?:tong|tổng)\b", low)) or "bao nhieu" in low
    asks_price = "gia" in low or "giá" in low
    return ParsedOrder(
        qty=qty,
        qty_confident=qty_confident,
        product=product,
        coupon=coupon,
        destination=destination,
        delivery_requested=delivery_requested,
        asks_total=asks_total,
        asks_price=asks_price,
    )


def _clarify_question(question: str, parsed: ParsedOrder) -> str:
    hints: list[str] = []
    if parsed.product:
        hints.append(f"san pham={parsed.product}")
    if parsed.qty_confident:
        hints.append(f"so luong={parsed.qty}")
    if parsed.coupon:
        hints.append(f"ma giam gia={parsed.coupon} (KHONG phai ten san pham)")
    if parsed.destination:
        hints.append(f"giao den={parsed.destination}")
    elif not parsed.delivery_requested:
        hints.append("khong co dia chi giao — KHONG goi calc_shipping")
    return f"{question} [Parse: {', '.join(hints)}]"


def _trace_observations(trace: list) -> tuple[dict | None, dict | None, dict | None]:
    stock = discount = shipping = None
    for step in trace or []:
        if not isinstance(step, dict):
            continue
        tool = step.get("tool")
        obs = step.get("observation") or {}
        if tool == "check_stock":
            if obs.get("found") and obs.get("in_stock"):
                stock = obs
            elif stock is None:
                stock = obs
        elif tool == "get_discount":
            discount = obs
        elif tool == "calc_shipping":
            if obs.get("cost_vnd") is not None and not obs.get("error"):
                shipping = obs
            elif shipping is None:
                shipping = obs
    return stock, discount, shipping


def _has_transient_tool_error(trace: list) -> bool:
    return any(
        isinstance(step, dict)
        and (step.get("observation") or {}).get("error") in _TRANSIENT_TOOL_ERRORS
        for step in (trace or [])
    )


def _shipping_weight_matches(stock: dict | None, shipping: dict | None, qty: int) -> bool:
    if not stock or not shipping:
        return False
    unit_weight = stock.get("weight_kg")
    used_weight = shipping.get("weight_kg")
    if unit_weight is None or used_weight is None:
        return False
    expected = float(unit_weight) * qty
    return abs(float(used_weight) - expected) < 1e-9


def _same_field(left, right) -> bool:
    return bool(left and right and _fold(str(left)) == _fold(str(right)))


def _needs_retry(result: dict, parsed: ParsedOrder) -> bool:
    if result.get("status") != "ok":
        return result.get("status") in _RETRYABLE
    trace = result.get("trace") or []
    if _has_transient_tool_error(trace):
        return True
    if parsed.destination and parsed.qty_confident and _compute_total(parsed, trace) is None:
        stock, _, shipping = _trace_observations(trace)
        if stock and stock.get("found") and stock.get("in_stock"):
            if shipping and shipping.get("error") not in (None, *_TRANSIENT_TOOL_ERRORS):
                return False
            return (
                not shipping
                or shipping.get("error") in _TRANSIENT_TOOL_ERRORS
                or shipping.get("cost_vnd") is None
                or not _shipping_weight_matches(stock, shipping, parsed.qty)
            )
    return False


def _retry_question(question: str, parsed: ParsedOrder, result: dict) -> str:
    stock, _, shipping = _trace_observations(result.get("trace") or [])
    if parsed.destination and parsed.qty_confident and stock and stock.get("weight_kg") is not None:
        expected = float(stock["weight_kg"]) * parsed.qty
        if not _shipping_weight_matches(stock, shipping, parsed.qty):
            return (
                f"{question} [RETRY: calc_shipping phai dung weight_kg={expected:g} "
                f"= {float(stock['weight_kg']):g}*{parsed.qty}; khong dung qty lam weight.]"
            )
    return f"{question} [RETRY: loi tool tam thoi; goi lai dung quy tac, khong doi du lieu.]"


def _compute_total(parsed: ParsedOrder, trace: list) -> ComputedTotal | None:
    if not parsed.product or not parsed.qty_confident:
        return None

    stock, discount, shipping = _trace_observations(trace)
    if not stock or not stock.get("found"):
        return None
    if not _same_field(stock.get("item"), parsed.product):
        return None
    available = int(stock.get("quantity") or 0)
    if stock.get("in_stock") is False or available < parsed.qty:
        return None

    unit = int(stock.get("unit_price_vnd") or 0)
    if unit <= 0:
        return None

    pct = 0
    if (
        parsed.coupon
        and discount
        and _same_field(discount.get("code"), parsed.coupon)
        and discount.get("valid")
    ):
        pct = int(discount.get("percent") or 0)

    subtotal = unit * parsed.qty
    after_discount = subtotal * (100 - pct) // 100

    ship_cost = 0
    if parsed.delivery_requested:
        if not shipping:
            return None
        if shipping.get("error") or shipping.get("cost_vnd") is None:
            return None
        if parsed.destination and not _same_field(shipping.get("destination"), parsed.destination):
            return None
        if not _shipping_weight_matches(stock, shipping, parsed.qty):
            return None
        ship_cost = int(shipping.get("cost_vnd") or 0)

    return ComputedTotal(
        total=after_discount + ship_cost,
        product=parsed.product,
        qty=parsed.qty,
        unit_price=unit,
        discount_pct=pct,
        shipping=ship_cost,
    )


def _refusal_text(parsed: ParsedOrder, trace: list) -> str:
    stock, _, shipping = _trace_observations(trace)
    if not parsed.product:
        return "San pham khong thuoc catalog. Khong the dat hang."
    if stock and stock.get("found") and stock.get("in_stock") is False:
        return f"{parsed.product} het hang. Khong the dat hang."
    if stock and stock.get("found") and int(stock.get("quantity") or 0) < parsed.qty:
        return f"{parsed.product} khong du so luong. Khong the dat hang."
    if stock and not stock.get("found"):
        return f"Khong tim thay {parsed.product}. Khong the dat hang."
    if parsed.delivery_requested and shipping and (shipping.get("error") or shipping.get("cost_vnd") is None):
        return f"Khu vuc {parsed.destination} khong duoc giao hang. Khong the tinh tong."
    return "Khong the xu ly don hang nay."


def _finalize_answer(question: str, answer: str | None, trace: list) -> str:
    parsed = _parse_order(question)
    computed = _compute_total(parsed, trace)
    if computed:
        body = (
            f"{computed.product} x{computed.qty}, "
            f"don gia {computed.unit_price:,} VND, giam {computed.discount_pct}%, "
            f"ship {computed.shipping:,} VND."
        ).replace(",", ".")
        return f"{body}\nTong cong: {computed.total} VND"
    stock, _, shipping = _trace_observations(trace)
    grounded_refusal = (
        not parsed.product
        or (stock is not None and not stock.get("found"))
        or (
            stock is not None
            and (
                stock.get("in_stock") is False
                or int(stock.get("quantity") or 0) < parsed.qty
            )
        )
        or (
            parsed.delivery_requested
            and shipping is not None
            and shipping.get("error") not in _TRANSIENT_TOOL_ERRORS
        )
    )
    if grounded_refusal:
        return _refusal_text(parsed, trace)
    return answer or "Khong the xu ly don hang nay."


def _cache_key(question: str, config: dict) -> str:
    model = config.get("model", "")
    prompt = config.get("system_prompt") or config.get("prompt_file", "")
    raw = f"{model}|{prompt}|{question}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _trace_tool_errors(trace: list) -> int:
    return sum(
        1
        for step in (trace or [])
        if isinstance(step, dict) and (step.get("observation") or {}).get("error")
    )


def _trace_repeated_actions(trace: list) -> bool:
    actions = [
        str(step.get("tool"))
        for step in (trace or [])
        if isinstance(step, dict) and step.get("tool")
    ]
    return len(actions) != len(set(actions))


def _redact_answer(answer: str | None) -> str | None:
    if not answer:
        return answer
    text, _ = redact(answer)
    return text


def _empty_result(status: str = "wrapper_error") -> dict:
    return {"answer": None, "status": status, "steps": 0, "trace": [], "meta": {}}


def _log_call(context: dict, result: dict, wall_ms: int, attempt: int) -> None:
    if not logger:
        return
    meta = result.get("meta") or {}
    usage = meta.get("usage") or {}
    trace = result.get("trace") or []
    answer = result.get("answer") or ""
    _, pii_hits = redact(answer)
    logger.log_event(
        "AGENT_CALL",
        {
            "qid": context.get("qid"),
            "session_id": context.get("session_id"),
            "turn_index": context.get("turn_index"),
            "attempt": attempt,
            "status": result.get("status"),
            "steps": result.get("steps"),
            "wall_ms": wall_ms,
            "latency_ms": meta.get("latency_ms"),
            "usage": usage,
            "cost_usd": cost_from_usage(meta.get("model", ""), usage),
            "tools_used": meta.get("tools_used", []),
            "tool_errors": _trace_tool_errors(trace),
            "repeated_tools": _trace_repeated_actions(trace),
            "pii_in_answer": pii_hits > 0,
        },
    )


def _log_wrapper_error(context: dict, question: str, exc: Exception) -> None:
    if not logger:
        return
    logger.log_event(
        "WRAPPER_ERROR",
        {
            "qid": context.get("qid"),
            "session_id": context.get("session_id"),
            "turn_index": context.get("turn_index"),
            "question": question,
            "error": repr(exc),
            "traceback": traceback.format_exc(),
        },
    )


def mitigate(call_next, question, config, context):
    cid = new_correlation_id()
    set_correlation_id(cid)

    try:
        conf = dict(config or {})
        raw = _sanitize_question(question)
        parsed = _parse_order(raw)
        clarified = _clarify_question(raw, parsed)

        turn = int((context or {}).get("turn_index") or 0)
        reset_every = int(conf.get("context_reset_every") or 0)
        if reset_every and turn and turn % reset_every == 0:
            base = (context or {}).get("session_id") or "session"
            conf["session_id"] = f"{base}-r{turn}"

        cache = (context or {}).get("cache")
        lock = (context or {}).get("cache_lock")
        key = _cache_key(clarified, conf)
        if cache is not None and conf.get("cache", {}).get("enabled"):
            if lock:
                with lock:
                    cached = cache.get(key)
            else:
                cached = cache.get(key)
            if cached is not None:
                if logger:
                    logger.log_event("CACHE_HIT", {"qid": (context or {}).get("qid"), "key": key[:12]})
                return deepcopy(cached)

        retry_cfg = conf.get("retry") or {}
        enabled = bool(retry_cfg.get("enabled"))
        max_attempts = int(retry_cfg.get("max_attempts") or 1) if enabled else 1
        backoff_ms = int(retry_cfg.get("backoff_ms") or 0)

        result = _empty_result()
        request = clarified
        for attempt in range(max_attempts):
            try:
                t0 = time.time()
                result = call_next(request, conf)
                wall_ms = int((time.time() - t0) * 1000)
                if not isinstance(result, dict):
                    raise TypeError(f"call_next returned {type(result).__name__}, expected dict")
                _log_call(context or {}, result, wall_ms, attempt)
            except Exception as exc:
                _log_wrapper_error(context or {}, clarified, exc)
                result = _empty_result()
                if attempt >= max_attempts - 1:
                    break
                if backoff_ms:
                    time.sleep(backoff_ms * (attempt + 1) / 1000.0)
                continue

            status = result.get("status", "")
            if status == "ok" and not _needs_retry(result, parsed):
                break
            if attempt >= max_attempts - 1:
                break
            if status not in _RETRYABLE and not (status == "ok" and _needs_retry(result, parsed)):
                break
            request = _retry_question(clarified, parsed, result)
            if backoff_ms:
                time.sleep(backoff_ms * (attempt + 1) / 1000.0)

        if result.get("status") == "ok":
            trace = result.get("trace") or []
            answer = _finalize_answer(raw, result.get("answer"), trace)
            result = dict(result)
            result["answer"] = answer

        if conf.get("redact_pii"):
            answer = result.get("answer")
            if answer:
                result = dict(result)
                result["answer"] = _redact_answer(answer)

        if cache is not None and conf.get("cache", {}).get("enabled") and result.get("status") == "ok":
            cached_result = deepcopy(result)
            if lock:
                with lock:
                    cache[key] = cached_result
            else:
                cache[key] = cached_result

        return result
    except Exception as exc:
        _log_wrapper_error(context or {}, _normalize(question), exc)
        return _empty_result()
