"""Real SoLEXS products become valid Observations, across the whole platform.

`| 17 | 17 | E5 | 900 | L | 15,12 | per-field vs spec | no imputation | parse fixtures |`

The path an Aditya-L1 X-ray measurement now takes, with each step performed by the component
that owns it:

  #16 ISSDC adapter       resolves a date to the day's archive and its products
  #10 provenance kernel   mints the digest of every product, and records the derivation
  #15 ingest contract     admits the acquisition; supplies the one sanctioned clock read
  #17 SoLEXS parsers      canonicalise a product into second-by-second Observations
  #12 domain model        holds the row, and refuses a fabricated absence
  #11 contract schemas    validate the serialised Observation
  #14 manifest            records the Tier 0 archive as referenced, never deposited
  #13 import rules        say Ingest may do all of this and reach no other context

TWO CLASSES OF TEST
-------------------
**Fixture tests** run everywhere. They use FITS products written by the test with the layout
`SPEC-parsers@r6` §2.1–2.3 records.

**Real-corpus tests** are marked `real_only` and skip where the archive is absent (STD-12,
E5 §17). They re-measure the spec's own `OBSERVED` values against the 2024-05-14 SDD2
products — the X8.7 flare day — so a claim in the specification and the behaviour of this
code are checked against each other rather than against nothing.

The guard tests for `.gz` **products**, never for a directory: five v1.1 archive directories
exist in a clean checkout because their quicklook PNGs are tracked, while the 3.5 GB of
science products are not.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import jsonschema
import pytest
from referencing import Registry, Resource

from contexts.ingest import verify_conformance
from contexts.ingest.adapters.issdc_pradan import IssdcPradanAdapter
from contexts.ingest.parsers.solexs import gti, lc, pi
from contexts.ingest.tests import solexs_fixtures as fx
from domain.entities import Observation
from domain.invariants import (
    absence_survives_serialisation,
    ingest_time_is_not_backfilled,
    observation_is_wellformed,
)
from domain.values import Digest, Identifier, Timestamp
from kernel.provenance import Digest as KernelDigest, ProvenanceStore, begin_run, digest_file

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"
REAL_ARCHIVE = REPO_ROOT / "research" / "data" / "aditya_l1" / "real_l1_v1" / "solexs"

FLARE_DAY = "2024-05-14"
#: §2.1 / §2.3 `OBSERVED` on 2024-05-14 SDD2. Re-measured by the real-corpus tests below.
SPEC_ABSENT_OFFSETS = (0, 5, 30_072, 30_078, 83_951)
SPEC_EXPOSURE = 86_395.0


def real_products_present() -> bool:
    if not REAL_ARCHIVE.is_dir():
        return False
    return any(p for p in REAL_ARCHIVE.rglob("*.gz") if not p.name.startswith("._"))


real_only = pytest.mark.skipif(
    not real_products_present(), reason="real SoLEXS archive not extracted"
)


def registry() -> Registry:
    built = Registry()
    for path in sorted(CONTRACTS.glob("*.schema.json")):
        if path.name.startswith("._"):
            continue
        built = Resource.from_contents(json.loads(path.read_text())) @ built
    return built


def validator_for(name: str):
    schema = json.loads((CONTRACTS / f"{name}.schema.json").read_text())
    return jsonschema.Draft202012Validator(schema, registry=registry())


def real_product(kind: str) -> Path:
    stem = REAL_ARCHIVE / "AL1_SLX_L1_20240514_v1.0" / "AL1_SLX_L1_20240514_v1.0"
    return stem / "SDD2" / f"AL1_SOLEXS_20240514_SDD2_L1.{kind}.gz"


# ═══════════════════════════════════════════ the full path, on fixtures


@pytest.fixture
def acquired(tmp_path):
    """A conforming acquisition of a fixture archive carrying real-shaped products."""
    root = tmp_path / "archive"
    directory = fx.sdd2(root)
    fx.write_lc(directory / "AL1_SOLEXS_20240514_SDD2_L1.lc.gz",
                counts=fx.nan_at(86_400, SPEC_ABSENT_OFFSETS))
    fx.write_gti(
        directory / "AL1_SOLEXS_20240514_SDD2_L1.gti.gz",
        intervals=_intervals_excluding(SPEC_ABSENT_OFFSETS),
    )
    store = ProvenanceStore(tmp_path / "store")
    adapter = IssdcPradanAdapter(root, store)
    return store, adapter, verify_conformance(adapter, selector=FLARE_DAY)


def _intervals_excluding(offsets: tuple[int, ...]) -> list[tuple[float, float]]:
    """GTI intervals covering the day except the given second-offsets.

    Built to the inclusive convention (§2.3 r1) so `Σ(STOP−START+1)` equals the covered
    second count exactly — the fixture is F-09-consistent by construction rather than by a
    tolerance.
    """
    excluded = set(offsets)
    intervals: list[tuple[float, float]] = []
    start: int | None = None
    for offset in range(86_400):
        if offset in excluded:
            if start is not None:
                intervals.append((fx.FLARE_DAY_TSTART + start,
                                  fx.FLARE_DAY_TSTART + offset - 1))
                start = None
        elif start is None:
            start = offset
    if start is not None:
        intervals.append((fx.FLARE_DAY_TSTART + start, fx.FLARE_DAY_TSTART + 86_399))
    return intervals


def test_an_acquired_product_becomes_contract_valid_observations(acquired, tmp_path):
    """The whole path: acquire → digest → parse → Observation → contract → provenance."""
    store, adapter, acquisition = acquired
    product = adapter.archive_for(FLARE_DAY) / "AL1_SLX_L1_20240514_v1.0" / "SDD2" / \
        "AL1_SOLEXS_20240514_SDD2_L1.lc.gz"

    # The kernel mints the product's digest — the parser never could (ADR-0005).
    minted = digest_file(product)
    curve = lc.parse(product, Digest(minted.hex))

    observations = product_observations(curve, acquisition)
    assert len(observations) == 86_400

    validator = validator_for("observation")
    for observation in observations[:200]:
        validator.validate(observation.to_dict())
        assert observation_is_wellformed(observation)

    # Every row traces to the exact bytes it was parsed from.
    assert {str(o.source_digest) for o in observations} == {minted.hex}

    # And the derivation is recorded, so a published number is answerable to the archive.
    run = begin_run(context="ingest", event="parse")
    canonical = store.put_bytes(
        json.dumps([o.to_dict() for o in observations[:10]], sort_keys=True).encode()
    )
    store.record(run, inputs=[KernelDigest(str(acquisition.artifact.digest))],
                 outputs=[canonical.digest])
    assert KernelDigest(str(acquisition.artifact.digest)) in store.ancestors(canonical.digest)


def product_observations(curve, acquisition) -> list[Observation]:
    return list(curve.observations(
        source_id=acquisition.provenance.source_id,
        ingest_time=acquisition.provenance.ingest_time,
    ))


def test_absence_survives_the_whole_path(acquired, tmp_path):
    """The no-imputation property, checked at the far end rather than at the parser.

    A NaN second becomes `value = None`, validates against the contract as `null`, survives
    serialisation, and is still distinguishable from a measured zero. Any layer that filled
    it would break exactly one of those four.
    """
    _, adapter, acquisition = acquired
    product = adapter.archive_for(FLARE_DAY) / "AL1_SLX_L1_20240514_v1.0" / "SDD2" / \
        "AL1_SOLEXS_20240514_SDD2_L1.lc.gz"
    curve = lc.parse(product, Digest(digest_file(product).hex))
    observations = product_observations(curve, acquisition)

    validator = validator_for("observation")
    for offset in SPEC_ABSENT_OFFSETS:
        absent = observations[offset]
        assert absent.value is None
        assert absent.value_is_absent
        document = absent.to_dict()
        validator.validate(document)
        assert document["value"] is None
        assert absence_survives_serialisation(absent)

    measured_zero = observations[1]
    assert measured_zero.value == 0.0
    assert not measured_zero.value_is_absent
    validator.validate(measured_zero.to_dict())
    assert measured_zero.to_dict()["value"] == 0.0


def test_the_ingest_time_comes_from_the_acquisition_not_the_parser(acquired, tmp_path):
    """ADR-0004/0022: the parser propagates a stamp; it never reads a clock or backfills."""
    _, adapter, acquisition = acquired
    product = adapter.archive_for(FLARE_DAY) / "AL1_SLX_L1_20240514_v1.0" / "SDD2" / \
        "AL1_SOLEXS_20240514_SDD2_L1.lc.gz"
    curve = lc.parse(product, Digest(digest_file(product).hex))

    stamped = product_observations(curve, acquisition)[100]
    assert stamped.ingest_time == acquisition.provenance.ingest_time
    assert ingest_time_is_not_backfilled(stamped, Timestamp("2026-05-01T00:00:00Z"))

    historical = next(iter(curve.observations(source_id=Identifier("issdc-pradan"),
                                              ingest_time=None)))
    assert historical.ingest_time is None
    validator_for("observation").validate(historical.to_dict())


def test_the_valid_time_is_the_second_the_sun_was_observed(acquired, tmp_path):
    """The epoch resolved from the file (§2.1), not assumed."""
    _, adapter, acquisition = acquired
    product = adapter.archive_for(FLARE_DAY) / "AL1_SLX_L1_20240514_v1.0" / "SDD2" / \
        "AL1_SOLEXS_20240514_SDD2_L1.lc.gz"
    curve = lc.parse(product, Digest(digest_file(product).hex))
    observations = product_observations(curve, acquisition)

    assert str(observations[0].valid_time) == "2024-05-14T00:00:00Z"
    assert str(observations[60_660].valid_time) == "2024-05-14T16:51:00Z"  # the X8.7 peak
    assert str(observations[-1].valid_time) == "2024-05-14T23:59:59Z"


def test_the_manifest_still_refuses_to_redistribute_the_parsed_archive(acquired):
    """Parsing does not change the tier: the bytes stay referenced (ADR-0023, STD-23)."""
    _, _, acquisition = acquired
    manifest = {
        "kind": "dataset", "digest": acquisition.artifact.digest.hex, "tier": 0,
        "recorded_at": str(acquisition.provenance.ingest_time),
        "retention": {"class": "permanent"},
        "retrieval": acquisition.artifact.retrieval.to_dict(),
    }
    validator_for("manifest").validate(manifest)

    redistributing = dict(manifest)
    redistributing["deposition"] = {
        "provider": "Zenodo", "url": "https://zenodo.org/records/1", "doi": None,
    }
    assert list(validator_for("manifest").iter_errors(redistributing))


def test_the_parsers_stay_inside_the_ingest_import_rule():
    """ADR-0026, and the one grant #17 added.

    `astropy` is now permitted to Ingest — reading FITS needs a FITS reader. Nothing else
    changed, and no context root was granted.
    """
    from tools.gates.imports import POLICIES, run

    report, code = run(POLICIES)
    assert code == 0, report.violations

    ingest = next(p for p in POLICIES if p.package == "contexts.ingest")
    assert ingest.allow == frozenset({"contracts", "domain", "kernel", "astropy"})
    assert "contexts" not in ingest.allow


# ═══════════════════════════════════════════ the real corpus


@real_only
def test_the_real_flare_day_lightcurve_reproduces_the_specification():
    """§2.1 `OBSERVED`, re-measured: 86,400 rows, 5 NaN at exactly the recorded offsets.

    The specification states these as observations of the archive. This asserts the parser
    reproduces them, so a drift in either the code or the archive is a red test rather than a
    quiet disagreement between a document and reality.
    """
    path = real_product("lc")
    curve = lc.parse(path, Digest(digest_file(path).hex))

    assert curve.header.rows == 86_400
    assert curve.header.tstart == 1_715_644_800.0
    assert str(lc.unix_to_timestamp(curve.header.tstart)) == "2024-05-14T00:00:00Z"
    assert curve.absent_offsets == SPEC_ABSENT_OFFSETS
    assert curve.n_absent == 5
    assert curve.n_finite == 86_395
    assert curve.instrument_id == Identifier("solexs-sdd2")


@real_only
def test_the_real_flare_day_gti_satisfies_the_exact_exposure_equality():
    """§2.3 / F-09: Σ(STOP−START+1) == EXPOSURE, tolerance 0 s.

    The inclusive convention's whole justification, measured on the day it was verified for.
    """
    path = real_product("gti")
    intervals = gti.parse(path, Digest(digest_file(path).hex))

    assert intervals.detector_active
    assert len(intervals.intervals) == 5
    assert intervals.live_time == SPEC_EXPOSURE == 86_395.0
    assert intervals.declared_exposure == SPEC_EXPOSURE
    assert intervals.live_time == intervals.declared_exposure


@real_only
def test_the_nan_set_equals_the_gti_excluded_set_on_the_reference_day():
    """§2.1 `OBSERVED`: on 2024-05-14 SDD2 the NaN set is exactly the GTI-excluded set.

    The r5 amendment withdrew *equality* as an archive-wide claim and replaced it with the
    implication `NaN ⇒ GTI-excluded`. This asserts only what §2.1 states for **this day**,
    and is deliberately not generalised: §2.3 §8 A-8 requires Milestone VIII to check all 436
    archives, and *"any deviation is a scientific finding and MUST terminate validation"*.

    Evaluating the implication across a day is the day-assembly layer's job (#19); this is
    the single-day observation the specification records.
    """
    lc_path, gti_path = real_product("lc"), real_product("gti")
    curve = lc.parse(lc_path, Digest(digest_file(lc_path).hex))
    intervals = gti.parse(gti_path, Digest(digest_file(gti_path).hex))

    excluded = intervals.excluded_seconds(curve.header.tstart, curve.header.rows)
    assert curve.absent_offsets == excluded == SPEC_ABSENT_OFFSETS
    assert curve.n_finite == intervals.declared_exposure


@real_only
def test_the_real_sdd1_gti_is_empty_and_that_is_legal():
    """F-12, the single deliberate non-terminating rule. §1.1 records SDD1 at zero rows."""
    path = REAL_ARCHIVE / "AL1_SLX_L1_20240514_v1.0" / "AL1_SLX_L1_20240514_v1.0" / \
        "SDD1" / "AL1_SOLEXS_20240514_SDD1_L1.gti.gz"
    intervals = gti.parse(path, Digest(digest_file(path).hex))

    assert intervals.detector_active is False
    assert intervals.intervals == ()
    assert intervals.detector == "SDD1"


@real_only
def test_the_real_spectra_declare_340_ordinal_channels():
    """§2.2: DETCHANS=340, CHANTYPE='PI', constant channel map, and no energy anywhere."""
    path = real_product("pi")
    spectra = pi.parse(path, Digest(digest_file(path).hex))

    assert spectra.header.detchans == 340
    assert spectra.header.chantype == "PI"
    assert spectra.channel_map == tuple(range(340))
    assert spectra.header.poisserr is False

    first = next(iter(spectra.spectra()))
    assert len(first.counts) == 340
    assert str(first.valid_time) == "2024-05-14T00:00:00Z"


@real_only
def test_the_real_spectra_and_lightcurve_agree_on_the_epoch():
    """V-PI-3 / F-06, on the real products."""
    lc_path, pi_path = real_product("lc"), real_product("pi")
    curve = lc.parse(lc_path, Digest(digest_file(lc_path).hex))
    spectra = pi.parse(pi_path, Digest(digest_file(pi_path).hex))
    pi.check_epoch_agrees_with_lightcurve(spectra, curve)
    assert spectra.first_tstart == curve.header.tstart


@real_only
def test_real_observations_validate_against_the_contract():
    """Real Aditya-L1 X-ray measurements, as contract-valid Observations.

    A sample rather than all 86,400: validating every row against a JSON Schema would take
    minutes and prove the same thing. The sample spans the day and includes every absent
    second the archive declares, which are the rows most likely to be mishandled.
    """
    path = real_product("lc")
    curve = lc.parse(path, Digest(digest_file(path).hex))
    observations = list(curve.observations(
        source_id=Identifier("issdc-pradan"),
        ingest_time=Timestamp("2024-06-16T09:00:00Z"),
    ))

    assert len(observations) == 86_400
    validator = validator_for("observation")
    sample = [observations[i] for i in (0, 1, 5, 30_072, 30_078, 60_660, 83_951, 86_399)]
    for observation in sample:
        validator.validate(observation.to_dict())
        assert observation_is_wellformed(observation)

    # The absent seconds are absent, and nothing else is.
    for offset in SPEC_ABSENT_OFFSETS:
        assert observations[offset].value is None
    assert observations[60_660].value is not None, "the flare peak minute is measured"


@real_only
def test_the_flare_peak_carries_a_real_measurement():
    """2024-05-14T16:51 UTC — the GOES X8.7 peak, and SALVAGE-001's reference event.

    The assertion is deliberately weak on physics: that the second is measured, finite and
    non-negative. §2.2 forbids stating a SoLEXS energy, and no response file exists, so any
    claim beyond "a count was recorded here" would exceed what the archive supports.
    """
    path = real_product("lc")
    curve = lc.parse(path, Digest(digest_file(path).hex))

    peak_offset = 16 * 3600 + 51 * 60
    value = curve.counts[peak_offset]
    assert value is not None
    assert math.isfinite(value) and value >= 0
    assert str(lc.unix_to_timestamp(curve.times[peak_offset])) == "2024-05-14T16:51:00Z"
