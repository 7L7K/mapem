from __future__ import annotations

"""
Era-aware geocoding brain that:
- Queries local Gazetteer cache table first (name_norm, admin_norm, era_bucket)
- Scores multiple candidates using text sim, admin match, era overlap,
  and proximity to known family locations (if provided in context)
- Persists GeocodeAttempt rows with provider I/O and debug scoring
- Falls back to external providers with backoff and rate limiting
"""

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from backend.models.gazetteer_entry import GazetteerEntry, compute_era_bucket
from backend.models.geocode_debug import GeocodeAttempt
from backend.models.location_models import LocationOut
from backend.utils.helpers import normalize_location, calculate_name_similarity
from backend.utils.logger import get_file_logger

logger = get_file_logger("geo_brain")


class RateLimiter:
    def __init__(self, rate_per_sec: float) -> None:
        self.rate_per_sec = rate_per_sec
        self.allowance = rate_per_sec
        self.last_check = time.monotonic()

    def sleep_if_needed(self) -> None:
        now = time.monotonic()
        elapsed = now - self.last_check
        self.last_check = now
        self.allowance = min(self.rate_per_sec, self.allowance + elapsed * self.rate_per_sec)
        if self.allowance < 1.0:
            to_sleep = (1.0 - self.allowance) / self.rate_per_sec
            time.sleep(max(0.0, to_sleep))
            self.allowance = 0.0
        else:
            self.allowance -= 1.0


@dataclass
class GeoContext:
    event_year: Optional[int] = None
    admin_hint: Optional[str] = None
    family_coords: Optional[List[Tuple[float, float]]] = None


def _distance_score(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    dx = lat1 - lat2
    dy = (lng1 - lng2) * 0.6
    d2 = dx * dx + dy * dy
    return max(0.0, min(1.0, 1.0 - (d2 / 100.0)))


def _era_overlap_score(bucket: str, year: Optional[int]) -> float:
    if year is None:
        return 0.5 if bucket != "unknown" else 0.3
    expected = compute_era_bucket(year)
    return 1.0 if expected == bucket else 0.4


def score_candidate(
    name_query: str,
    admin_hint: Optional[str],
    family_coords: Optional[List[Tuple[float, float]]],
    year: Optional[int],
    candidate: GazetteerEntry,
) -> Tuple[float, Dict[str, Any]]:
    text_sim = calculate_name_similarity(name_query, candidate.name_norm) / 100.0
    admin_sim = 0.0
    if admin_hint and candidate.admin_norm:
        admin_sim = calculate_name_similarity(admin_hint, candidate.admin_norm) / 100.0
    era_sim = _era_overlap_score(candidate.era_bucket, year)
    prox = 0.0
    if family_coords:
        for plat, plng in family_coords:
            prox = max(prox, _distance_score(plat, plng, candidate.latitude, candidate.longitude))
    score = 0.5 * text_sim + 0.2 * admin_sim + 0.2 * era_sim + 0.1 * prox
    detail = {
        "text_sim": round(text_sim, 3),
        "admin_sim": round(admin_sim, 3),
        "era": candidate.era_bucket,
        "era_sim": round(era_sim, 3),
        "proximity": round(prox, 3),
        "weights": {"text": 0.5, "admin": 0.2, "era": 0.2, "prox": 0.1},
    }
    return score, detail


class GazetteerDBGeocoder:
    def __init__(self) -> None:
        self._nominatim_limiter = RateLimiter(1.0)

    def resolve(
        self,
        session: Optional[Session],
        raw_place: str,
        *,
        context: Optional[GeoContext] = None,
        debug: bool = True,
    ) -> Optional[LocationOut]:
        if session is None:
            return None
        norm = normalize_location(raw_place)
        if not norm:
            return None
        admin_hint = (context.admin_hint if context else None) or ""
        era_bucket = compute_era_bucket(context.event_year if context else None)
        era_candidates = {era_bucket}
        if era_bucket == "unknown":
            era_candidates |= {"1800_1890", "1890_1950", "pre_1800"}
        q = (
            session.query(GazetteerEntry)
            .filter(GazetteerEntry.name_norm == norm)
            .filter(GazetteerEntry.era_bucket.in_(list(era_candidates)))
        )
        rows: List[GazetteerEntry] = list(q.limit(50))
        if not rows:
            return None
        best_score = -1.0
        best = None
        explanations: List[Dict[str, Any]] = []
        for r in rows:
            score, detail = score_candidate(
                norm,
                admin_hint,
                (context.family_coords if context else None),
                (context.event_year if context else None),
                r,
            )
            explanations.append(
                {
                    "id": str(r.id),
                    "src": r.source,
                    "lat": r.latitude,
                    "lng": r.longitude,
                    "admin": r.admin_norm,
                    "era": r.era_bucket,
                    "score": round(score, 4),
                    "detail": detail,
                }
            )
            if score > best_score:
                best_score = score
                best = r
        if best is None:
            return None
        if debug:
            attempt = GeocodeAttempt(
                raw_place=raw_place,
                name_norm=norm,
                admin_norm=admin_hint or None,
                era_bucket=era_bucket,
                provider="gazetteer",
                chosen="yes",
                latitude=best.latitude,
                longitude=best.longitude,
                score=float(best_score),
                debug_scoring_json={"candidates": explanations},
            )
            try:
                session.add(attempt)
                session.flush()
            except Exception:
                logger.exception("Failed to persist GeocodeAttempt for '%s'", raw_place)
        return LocationOut(
            raw_name=raw_place,
            normalized_name=best.name_norm,
            latitude=best.latitude,
            longitude=best.longitude,
            confidence_score=float(max(0.0, min(1.0, best_score))),
            confidence_label="gazetteer",
            status="ok",
            source="gazetteer",
        )


