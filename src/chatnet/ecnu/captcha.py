"""Optional CAPTCHA recognition helpers for ECNU login automation."""

from __future__ import annotations

import io
from collections import defaultdict
from typing import Any


def _load_ocr_deps() -> tuple[Any, Any, Any]:
    try:
        import ddddocr
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError(
            'CAPTCHA auto-login requires optional dependencies. Install them with: pip install "ChatNet[captcha]"'
        ) from exc
    return ddddocr, np, Image


def recognize_captcha_topk(image_bytes: bytes, topk: int = 5, expected_length: int = 4) -> list[str]:
    ddddocr, _, _ = _load_ocr_deps()
    ocr = ddddocr.DdddOcr(show_ad=False)
    variants = build_variants(image_bytes)
    variant_results = {
        name: topk_for_variant(ocr, data, expected_length=expected_length)
        for name, data in variants.items()
    }
    aggregate = aggregate_variant_candidates(variant_results, topk=topk)
    return [row["text"] for row in aggregate]


def pil_to_bytes(image: Any) -> bytes:
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def dilate(mask: Any, iterations: int = 1) -> Any:
    _, np, _ = _load_ocr_deps()
    out = mask.copy()
    for _ in range(iterations):
        padded = np.pad(out, 1, constant_values=False)
        grown = np.zeros_like(out)
        for dy in range(3):
            for dx in range(3):
                grown |= padded[dy : dy + out.shape[0], dx : dx + out.shape[1]]
        out = grown
    return out


def erode(mask: Any, iterations: int = 1) -> Any:
    _, np, _ = _load_ocr_deps()
    out = mask.copy()
    for _ in range(iterations):
        padded = np.pad(out, 1, constant_values=True)
        shrunk = np.ones_like(out)
        for dy in range(3):
            for dx in range(3):
                shrunk &= padded[dy : dy + out.shape[0], dx : dx + out.shape[1]]
        out = shrunk
    return out


def closing(mask: Any, iterations: int = 1) -> Any:
    return erode(dilate(mask, iterations), iterations)


def mask_bbox(mask: Any) -> tuple[int, int, int, int] | None:
    _, np, _ = _load_ocr_deps()
    ys, xs = np.where(mask)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def build_variants(image_bytes: bytes) -> dict[str, bytes]:
    _, np, Image = _load_ocr_deps()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    arr = np.array(image, dtype=np.uint8)
    mean = arr.mean(axis=2)
    spread = arr.max(axis=2) - arr.min(axis=2)
    text_loose = (spread < 40) & (mean > 60)
    text_tight = (spread < 30) & (mean > 95)
    text_closed = closing(text_loose, iterations=1)
    variants = {
        "original": pil_to_bytes(image),
        "text_loose": pil_to_bytes(Image.fromarray((text_loose.astype(np.uint8) * 255), mode="L")),
        "text_tight": pil_to_bytes(Image.fromarray((text_tight.astype(np.uint8) * 255), mode="L")),
        "text_closed": pil_to_bytes(Image.fromarray((text_closed.astype(np.uint8) * 255), mode="L")),
    }
    bbox = mask_bbox(text_closed)
    if bbox is not None:
        x1, y1, x2, y2 = bbox
        crop = Image.fromarray((text_closed[y1 : y2 + 1, x1 : x2 + 1].astype(np.uint8) * 255), mode="L")
        nearest = getattr(getattr(Image, "Resampling", Image), "NEAREST")
        variants["text_closed_crop_x6"] = pil_to_bytes(
            crop.resize((crop.width * 6, crop.height * 6), nearest)
        )
    return variants


def logsumexp_pair(a: float, b: float) -> float:
    _, np, _ = _load_ocr_deps()
    if a == -np.inf:
        return b
    if b == -np.inf:
        return a
    m = a if a > b else b
    return float(m + np.log(np.exp(a - m) + np.exp(b - m)))


def ctc_prefix_beam_search(
    probs: Any,
    digit_indices: list[int],
    index_to_digit: dict[int, str],
    beam_size: int = 25,
    topk: int = 5,
    expected_length: int = 4,
    blank_index: int = 0,
) -> list[dict[str, Any]]:
    _, np, _ = _load_ocr_deps()
    beam: dict[str, tuple[float, float]] = {"": (0.0, -np.inf)}
    for t in range(probs.shape[0]):
        next_beam: dict[str, tuple[float, float]] = defaultdict(lambda: (-np.inf, -np.inf))
        for prefix, (p_b, p_nb) in beam.items():
            total = logsumexp_pair(p_b, p_nb)
            nb = next_beam[prefix]
            next_beam[prefix] = (
                logsumexp_pair(nb[0], total + float(np.log(probs[t, blank_index] + 1e-12))),
                nb[1],
            )
            if len(prefix) > expected_length:
                continue
            for idx in digit_indices:
                digit = index_to_digit[idx]
                p = float(np.log(probs[t, idx] + 1e-12))
                last = prefix[-1] if prefix else None
                if digit == last:
                    nb = next_beam[prefix]
                    next_beam[prefix] = (nb[0], logsumexp_pair(nb[1], p_nb + p))
                    new_prefix = prefix + digit
                    if len(new_prefix) <= expected_length:
                        nb2 = next_beam[new_prefix]
                        next_beam[new_prefix] = (nb2[0], logsumexp_pair(nb2[1], p_b + p))
                else:
                    new_prefix = prefix + digit
                    if len(new_prefix) <= expected_length:
                        nb2 = next_beam[new_prefix]
                        next_beam[new_prefix] = (nb2[0], logsumexp_pair(nb2[1], total + p))
        ranked = sorted(next_beam.items(), key=lambda kv: logsumexp_pair(kv[1][0], kv[1][1]), reverse=True)
        beam = dict(ranked[:beam_size])
    finals = []
    for prefix, (p_b, p_nb) in beam.items():
        if len(prefix) == expected_length:
            finals.append({"text": prefix, "logprob": logsumexp_pair(p_b, p_nb)})
    finals.sort(key=lambda row: row["logprob"], reverse=True)
    return finals[:topk]


def topk_for_variant(ocr: Any, img: bytes, expected_length: int = 4) -> dict[str, Any]:
    _, np, _ = _load_ocr_deps()
    result = ocr.classification(img, probability=True)
    probs = np.array(result["probabilities"], dtype=np.float64)
    if probs.ndim == 3:
        probs = probs[:, 0, :]
    charset = result["charset"]
    digit_indices = [i for i, ch in enumerate(charset) if ch.isdigit()]
    index_to_digit = {i: charset[i] for i in digit_indices}
    candidates = ctc_prefix_beam_search(probs, digit_indices, index_to_digit, expected_length=expected_length)
    return {"text": result["text"], "confidence": result["confidence"], "candidates": candidates}


def aggregate_variant_candidates(variant_results: dict[str, dict[str, Any]], topk: int = 5) -> list[dict[str, Any]]:
    scores: dict[str, float] = defaultdict(float)
    support: dict[str, int] = defaultdict(int)
    for result in variant_results.values():
        for rank, row in enumerate(result["candidates"]):
            scores[row["text"]] += row["logprob"]
            support[row["text"]] += max(0, topk - rank)
    ranked = sorted(scores, key=lambda text: (support[text], scores[text]), reverse=True)
    return [{"text": text, "score": scores[text], "support": support[text]} for text in ranked[:topk]]
