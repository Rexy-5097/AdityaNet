"""
app/services/operations/impact.py

Sprint 5.5 — ISRO Mission Impact Catalog

Provides dynamic mission impact assessments for the three primary ISRO
spacecraft affected by solar energetic particle (SEP) events and X-ray
flux increases associated with M/X-class flares.

Missions modelled:
  - Aditya-L1    : Solar observatory at L1 Lagrange point.
  - INSAT-3DR    : Geo-stationary meteorological/communication satellite.
  - Cartosat-3   : High-resolution Earth observation satellite (LEO).

Alert → Action mapping is modulated by probability and uncertainty so that
operators receive proportional, context-sensitive recommendations rather
than binary on/off warnings.
"""

from __future__ import annotations
import logging

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# Mission Definitions
# ──────────────────────────────────────────────────────────────────────────────

MISSION_CATALOG = {
    "Aditya-L1": {
        "description": "ISRO solar observatory at Sun-Earth L1 point (~1.5M km from Earth)",
        "orbit_type":  "Halo orbit, L1",
        "primary_risk": "Instrument saturation from X-ray flux surge; SEP damage to detectors",
        "actions": {
            "GREEN": [
                "Normal science operations. Monitor GOES X-ray flux in background.",
                "Ensure real-time telemetry link is nominal.",
            ],
            "YELLOW": [
                "Alert science operations team of elevated flare probability.",
                "Pre-configure safe-mode triggers on SUIT and HEL1OS instruments.",
                "Increase GOES X-ray telemetry cadence to 1-minute polling.",
                "Begin logging enhanced solar wind speed and proton flux data.",
            ],
            "RED": [
                "Immediately notify Spacecraft Operations Centre (SOC) Bengaluru.",
                "Switch SUIT (Solar UV Imaging Telescope) to safe-mode attenuator.",
                "Pause ASPEX particle data collection to avoid detector saturation.",
                "Activate HEL1OS hard X-ray background subtraction protocol.",
                "Increase downlink priority for real-time energetic particle data.",
                "Place instrument operations team on 30-minute standby recall.",
            ],
        },
        "recovery_time_hours": {"GREEN": 0, "YELLOW": 0, "RED": 2},
    },
    "INSAT-3DR": {
        "description": "Geostationary meteorological & communication relay satellite (GEO, 74°E)",
        "orbit_type":  "Geostationary, 74°E",
        "primary_risk": "Radio frequency interference from ionospheric disturbance; SEP latch-up in CMOS electronics",
        "actions": {
            "GREEN": [
                "Normal meteorological imaging and data relay operations.",
                "No additional protective action required.",
            ],
            "YELLOW": [
                "Alert ground mission operations team at SAC Ahmedabad.",
                "Review power subsystem status and battery charge state.",
                "Check IMAGER instrument health and prepare contingency mode.",
                "Activate ionospheric monitoring alert for transponder team.",
            ],
            "RED": [
                "Notify INSAT Control Centre immediately.",
                "Switch to eclipse-safe thermal configuration.",
                "Suspend non-critical transponder loads to maintain power margin.",
                "Monitor SEP particle flux threshold on satellite onboard memory.",
                "Prepare single-event latch-up (SEL) recovery procedure for execution.",
                "Issue advisory to DoorDarshan and Weather Services to expect brief data outage.",
            ],
        },
        "recovery_time_hours": {"GREEN": 0, "YELLOW": 0, "RED": 4},
    },
    "Cartosat-3": {
        "description": "High-resolution optical Earth observation satellite (LEO, ~509 km, SSO)",
        "orbit_type":  "Sun-synchronous LEO, ~509 km",
        "primary_risk": "Increased atmospheric drag from thermosphere expansion; radiation belt enhancement during post-flare storm",
        "actions": {
            "GREEN": [
                "Normal imaging operations. No restrictions.",
                "Maintain scheduled imaging passes over target areas.",
            ],
            "YELLOW": [
                "Alert NRSC ground station operators.",
                "Check onboard GPS orbit determination for potential thermosphere drag error.",
                "Review TLE accuracy and schedule fresh orbit determination upload if stale (> 6 hr).",
                "Postpone non-critical manoeuvres for 12 hours as precaution.",
            ],
            "RED": [
                "Immediately notify ISAC satellite operations team.",
                "Suspend all imaging operations and stow camera payload.",
                "Initiate drag compensation calculation using updated NRLMSISE-00 atmosphere model.",
                "Upload updated collision avoidance manoeuvre timeline within 2 hours.",
                "Activate safe mode on payload to prevent radiation-induced bit-flip errors.",
                "Increase station contact frequency from 2 to 4 passes per day.",
            ],
        },
        "recovery_time_hours": {"GREEN": 0, "YELLOW": 0, "RED": 6},
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# Impact Assessment Generator
# ──────────────────────────────────────────────────────────────────────────────

def _urgency_modifier(probability: float, uncertainty: float, alert_level: str) -> str:
    """
    Generate a human-readable urgency qualifier based on probability and uncertainty.
    """
    if alert_level == "GREEN":
        return "Routine monitoring."
    elif alert_level == "YELLOW":
        if probability >= 0.50:
            return f"Elevated risk (P={probability:.0%}). Precautionary actions strongly advised."
        else:
            return f"Moderate risk (P={probability:.0%}). Monitor closely and pre-position teams."
    else:  # RED
        if uncertainty > 0.10:
            return (
                f"High flare probability (P={probability:.0%}) with elevated model uncertainty "
                f"(σ={uncertainty:.3f}). Protective actions are required but may be re-evaluated "
                "in 30 minutes if probability stabilises."
            )
        else:
            return (
                f"High confidence RED alert (P={probability:.0%}, σ={uncertainty:.3f}). "
                "Execute all protective actions immediately."
            )


def get_mission_impact_assessment(
    alert_level: str,
    probability: float,
    uncertainty: float,
) -> dict:
    """
    Generate a mission impact assessment for all catalogued ISRO missions.

    Args:
        alert_level:  "GREEN", "YELLOW", or "RED"
        probability:  Calibrated flare probability [0, 1]
        uncertainty:  MC Dropout std uncertainty [0, 1]

    Returns:
        dict: {
            "alert_level": str,
            "urgency_summary": str,
            "missions": {
                "<mission_name>": {
                    "description": str,
                    "orbit_type": str,
                    "primary_risk": str,
                    "recommended_actions": List[str],
                    "estimated_recovery_time_hours": int,
                }
            }
        }
    """
    alert_level = alert_level.upper()
    if alert_level not in ("GREEN", "YELLOW", "RED"):
        logger.warning(f"Unknown alert_level '{alert_level}'. Defaulting to GREEN.")
        alert_level = "GREEN"

    urgency = _urgency_modifier(probability, uncertainty, alert_level)

    missions_out = {}
    for mission_name, catalog_entry in MISSION_CATALOG.items():
        missions_out[mission_name] = {
            "description":                    catalog_entry["description"],
            "orbit_type":                     catalog_entry["orbit_type"],
            "primary_risk":                   catalog_entry["primary_risk"],
            "recommended_actions":            catalog_entry["actions"][alert_level],
            "estimated_recovery_time_hours":  catalog_entry["recovery_time_hours"][alert_level],
        }

    return {
        "alert_level":    alert_level,
        "urgency_summary": urgency,
        "missions":       missions_out,
    }
