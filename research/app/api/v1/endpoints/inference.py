"""
app/api/v1/endpoints/inference.py

Sprint 5.5 — Updated Nowcast API Endpoint

New response fields:
  - confidence_level:          HIGH / MEDIUM / LOW
  - top_attention_patches:     list of top-3 attended patches with timestamps
                               and physical context
  - mission_impact:            ISRO mission impact assessment dict
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from pydantic import BaseModel, Field
from app.db.session import get_session
from app.models.flare import FlareEvent
from app.services.ml.inference import SuryaNetInferenceService

logger = logging.getLogger(__name__)

router = APIRouter()

# Lazy-loaded global service instance
_service: Optional[SuryaNetInferenceService] = None


def get_inference_service() -> SuryaNetInferenceService:
    global _service
    if _service is None:
        try:
            _service = SuryaNetInferenceService()
        except Exception as e:
            logger.error(f"Failed to initialize SuryaNetInferenceService: {e}")
            raise HTTPException(
                status_code=500,
                detail="ML model or calibrator failed to load on server.",
            )
    return _service


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic Schemas
# ──────────────────────────────────────────────────────────────────────────────

class FluxRecord(BaseModel):
    timestamp:  str   = Field(..., description="ISO 8601 UTC timestamp")
    short_flux: float = Field(..., description="Short channel X-ray flux (0.05-0.4 nm)")
    long_flux:  float = Field(..., description="Long channel X-ray flux (0.1-0.8 nm)")


class NowcastRequest(BaseModel):
    flux_history: List[FluxRecord] = Field(
        ...,
        description=(
            "Chronological flux records. "
            "Must contain between 360 and 362 one-minute records."
        ),
    )


class PhysicalContext(BaseModel):
    flux_value_W_m2:        float = Field(..., description="Long-channel flux at patch centre (W/m²)")
    flux_gradient_W_m2_min: float = Field(..., description="dFlux/dt at patch centre (W/m²/min)")
    rolling_variance_30min: float = Field(..., description="30-min flux variance at patch centre")


class AttentionPatch(BaseModel):
    rank:             int            = Field(..., description="Attention rank (1 = most attended)")
    patch_index:      int            = Field(..., description="0-based patch index (0–43)")
    timestamp:        str            = Field(..., description="Timestamp of patch centre")
    attention_share:  float          = Field(..., description="Fraction of total CLS attention")
    physical_context: PhysicalContext


class MissionImpact(BaseModel):
    alert_level:     str              = Field(..., description="Alert level applied")
    urgency_summary: str              = Field(..., description="Human-readable urgency description")
    missions:        Dict[str, Any]   = Field(..., description="Per-mission impact and recommended actions")


class NowcastResponse(BaseModel):
    alert_level:            str                     = Field(...,  description="Operational alert: GREEN, YELLOW, or RED")
    probability:            float                   = Field(...,  description="Calibrated flare probability")
    uncertainty:            float                   = Field(...,  description="Epistemic uncertainty (MC Dropout std)")
    uncertainty_level:      str                     = Field(...,  description="Uncertainty tier: LOW, MEDIUM, or HIGH")
    confidence_level:       str                     = Field(...,  description="Confidence level: HIGH, MEDIUM, or LOW")
    confirmation:           str                     = Field(...,  description="CONFIRMED or UNCONFIRMED (RED only)")
    model_version:          str                     = Field("patchtst_v1", description="Model version")
    forecast_horizon_hours: int                     = Field(6,    description="Prediction horizon (hours)")
    top_attention_patches:  List[AttentionPatch]    = Field([],   description="Top-3 CLS attention patches")
    mission_impact:         Optional[MissionImpact] = Field(None, description="ISRO mission impact assessment")


# ──────────────────────────────────────────────────────────────────────────────
# Nowcast Prediction Endpoint
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/nowcast", response_model=NowcastResponse)
async def predict_nowcast(
    request: NowcastRequest,
    service: SuryaNetInferenceService = Depends(get_inference_service),
    session: AsyncSession = Depends(get_session),
):
    """
    Operational nowcast: binary M/X solar flare risk for the next 6 hours.

    Accepts 360–362 one-minute GOES flux records. Returns calibrated
    probability, tiered alert level, attention-based explainability,
    and ISRO mission impact assessment.
    """
    n_records = len(request.flux_history)
    if n_records < 360 or n_records > 362:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid history length. Must be 360–362 records. Got {n_records}."
            ),
        )

    # 1. Convert payload to DataFrame
    try:
        data = [
            {
                "timestamp":  r.timestamp,
                "short_flux": r.short_flux,
                "long_flux":  r.long_flux,
            }
            for r in request.flux_history
        ]
        df = pd.DataFrame(data)
    except Exception as e:
        logger.error(f"Failed to parse input records: {e}")
        raise HTTPException(status_code=400, detail="Invalid request payload structure.")

    # 2. Query recent M/X flare times from TimescaleDB (last 7 days)
    try:
        t_max = pd.to_datetime(request.flux_history[-1].timestamp).tz_localize(None)
        start_lookup = t_max - timedelta(minutes=10080)  # 7 days
        stmt = (
            select(FlareEvent.start_time)
            .where(
                FlareEvent.start_time >= start_lookup,
                FlareEvent.start_time <= t_max,
                (
                    FlareEvent.flare_class.like("M%")
                    | FlareEvent.flare_class.like("X%")
                ),
            )
            .order_by(FlareEvent.start_time.asc())
        )
        db_res     = await session.execute(stmt)
        flare_times = list(db_res.scalars().all())
    except Exception as db_err:
        logger.warning(
            f"DB flare query failed, continuing without flare history: {db_err}"
        )
        flare_times = None

    # 3. Run inference
    try:
        pred = service.predict(df, flare_times=flare_times, include_explainability=True)
    except ValueError as val_err:
        logger.error(f"Input validation error: {val_err}")
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Prediction pipeline error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal prediction pipeline error.")

    # 4. Derive uncertainty tier label
    unc = pred["uncertainty_std"]
    if unc < 0.04:
        unc_level = "LOW"
    elif unc <= 0.10:
        unc_level = "MEDIUM"
    else:
        unc_level = "HIGH"

    # 5. Build attention patch response objects
    attention_patch_objects = []
    for p in pred.get("top_attention_patches", []):
        phys = p.get("physical_context", {})
        attention_patch_objects.append(
            AttentionPatch(
                rank=p["rank"],
                patch_index=p["patch_index"],
                timestamp=p["timestamp"],
                attention_share=p["attention_share"],
                physical_context=PhysicalContext(
                    flux_value_W_m2=phys.get("flux_value_W_m2", 0.0),
                    flux_gradient_W_m2_min=phys.get("flux_gradient_W_m2_min", 0.0),
                    rolling_variance_30min=phys.get("rolling_variance_30min", 0.0),
                ),
            )
        )

    # 6. Build mission impact response (if available)
    impact_obj = None
    raw_impact = pred.get("mission_impact")
    if raw_impact:
        impact_obj = MissionImpact(
            alert_level=raw_impact.get("alert_level", pred["alert_level"]),
            urgency_summary=raw_impact.get("urgency_summary", ""),
            missions=raw_impact.get("missions", {}),
        )

    # 7. Build and return response
    return NowcastResponse(
        alert_level=pred["alert_level"],
        probability=pred["calibrated_probability"],
        uncertainty=unc,
        uncertainty_level=unc_level,
        confidence_level=pred.get("confidence_level", "LOW"),
        confirmation=pred.get("confirmation", "CONFIRMED"),
        model_version="patchtst_v1",
        forecast_horizon_hours=6,
        top_attention_patches=attention_patch_objects,
        mission_impact=impact_obj,
    )
