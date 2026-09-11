"""Real HEL1OS products through the whole platform, coexisting with SoLEXS.

`| 18 | 18 | E5 | 900 | L | 17 | per-field vs spec | no imputation | parse fixtures |`

  #16 ISSDC adapter       the acquisition boundary the archive arrives through
  #10 provenance kernel   mints every digest, records the derivation
  #15 ingest contract     supplies the one sanctioned clock read
  #18 HEL1OS parsers      canonicalise five product types
  #12 domain model        holds the rows and both times
  #11 contract schemas    validate the serialised Observations
  #14 manifest            records the Tier 0 orbit as referenced, never deposited
  #13 import rules        say Ingest may do this and reach no other context

COEXISTENCE WITHOUT LEAKAGE IS THE POINT OF THIS FILE
------------------------------------------------------
SoLEXS and HEL1OS disagree on nearly every convention — counts vs rates, undeclared vs
declared units, Unix seconds vs MJD, PI(340) vs PHA(341)/PHA(511), uppercase vs lowercase
column names. F-07 and F-11 exist because assuming a shared convention across them is the
specific error that has already been made.

So the tests below put both instruments' Observations in one collection and assert that
every distinguishing fact survives: instrument identity, unit, quantity name, channel space
and time encoding. Nothing merges them, and nothing can.

Real-corpus tests skip where the archive is absent (STD-12, E5 §17); the guard tests for
`.fits` **products**, never a directory — `aux/cztdis/*.txt` files are tracked in git while
the 132 GB of FITS are not, which is the trap E5 §16 names by name.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from referencing import Registry, Resource

from contexts.ingest.parsers.hel1os import events, gti, hk, lc, orbit, spectra
from contexts.ingest.parsers.solexs import lc as solexs_lc
from contexts.ingest.parsers.solexs import pi as solexs_pi
from contexts.ingest.tests import hel1os_fixtures as fx
from contexts.ingest.tests import solexs_fixtures as sfx
from domain.entities import Observation
from domain.errors import ContractViolation
from domain.invariants import observation_is_wellformed
from domain.values import Digest, Identifier, Timestamp
from kernel.provenance import (
    Digest as KernelDigest,
    ProvenanceStore,
    begin_run,
    digest_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = REPO_ROOT / "contracts"
HEL1OS_ROOT = REPO_ROOT / "research" / "data" / "aditya_l1" / "real_l1_v1" / "hel1os"
SOLEXS_ROOT = REPO_ROOT / "research" / "data" / "aditya_l1" / "real_l1_v1" / "solexs"

#: The reference orbit §2.5–2.9 record their OBSERVED values against.
REFERENCE_ORBIT = "HLS_20251208_000008_43178sec_lev1_V111"


def real_orbit_present() -> bool:
    """Products, not directories — E5 §16.

    `aux/cztdis/*.txt` pixel maps are tracked in git while the FITS are not, so the orbit
    directory exists in a clean checkout and an `isdir` guard would pass where the data does
    not exist. That exact guard silently disabled 188 tests once.
    """
    if not HEL1OS_ROOT.is_dir():
        return False
    return any(p for p in HEL1OS_ROOT.rglob("*.fits") if not p.name.startswith("._"))


real_only = pytest.mark.skipif(
    not real_orbit_present(), reason="real HEL1OS orbit archive not extracted"
)
solexs_only = pytest.mark.skipif(
    not (SOLEXS_ROOT.is_dir()
         and any(p for p in SOLEXS_ROOT.rglob("*.gz") if not p.name.startswith("._"))),
    reason="real SoLEXS archive not extracted",
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


def orbit_dir() -> Path:
    return HEL1OS_ROOT / REFERENCE_ORBIT / "2025" / "12" / "08" / REFERENCE_ORBIT


# ═══════════════════════════════════════════ the whole path, on fixtures


def test_hel1os_rates_become_contract_valid_observations(tmp_path):
    """Parse → domain → contract → provenance, with the digest carried throughout."""
    store = ProvenanceStore(tmp_path / "store")
    path = fx.write_lightcurve(tmp_path / "lightcurve_czt1.fits", rows=60)
    minted = digest_file(path)
    registered = store.put_file(path)

    curve = lc.parse(path, Digest(minted.hex), detector="czt1")
    observations = list(curve.observations(
        source_id=Identifier("issdc-pradan"),
        ingest_time=Timestamp("2025-12-20T09:00:00Z"),
    ))

    # Five bands × 60 samples.
    assert len(observations) == 5 * 60

    validator = validator_for("observation")
    for observation in observations[:40]:
        validator.validate(observation.to_dict())
        assert observation_is_wellformed(observation)

    assert {str(o.source_digest) for o in observations} == {minted.hex}
    assert store.has_artifact(KernelDigest(minted.hex))
    assert registered.digest.hex == minted.hex

    run = begin_run(context="ingest", event="parse")
    canonical = store.put_bytes(
        json.dumps([o.to_dict() for o in observations[:5]], sort_keys=True).encode())
    store.record(run, inputs=[minted], outputs=[canonical.digest])
    assert minted in store.ancestors(canonical.digest)


def test_the_orbit_becomes_a_valid_tier_0_manifest(tmp_path):
    """ADR-0023: an orbit archive is referenced, never deposited."""
    path = fx.write_lightcurve(tmp_path / "lightcurve_czt1.fits", rows=10)
    minted = digest_file(path)

    manifest = {
        "kind": "dataset", "digest": minted.hex, "tier": 0,
        "recorded_at": "2025-12-20T09:00:00Z",
        "retention": {"class": "permanent"},
        "retrieval": {"provider": "ISSDC PRADAN",
                      "locator": f"hel1os/{REFERENCE_ORBIT}",
                      "requires_credentials": True},
    }
    validator_for("manifest").validate(manifest)

    redistributing = dict(manifest)
    redistributing["deposition"] = {
        "provider": "Zenodo", "url": "https://zenodo.org/records/1", "doi": None}
    assert list(validator_for("manifest").iter_errors(redistributing))


def test_the_parsers_stay_inside_the_ingest_import_rule():
    """ADR-0026, against the shipped policy."""
    from tools.gates.imports import POLICIES, run

    report, code = run(POLICIES)
    assert code == 0, report.violations

    ingest = next(p for p in POLICIES if p.package == "contexts.ingest")
    internal = ingest.allow & {"contracts", "domain", "kernel", "contexts", "apps",
                               "tools", "registry", "tests"}
    assert internal == {"contracts", "domain", "kernel"}
    assert "contexts" not in ingest.allow


# ═══════════════════════════════════════════ coexistence without leakage


def test_both_instruments_coexist_in_one_collection(tmp_path):
    """SoLEXS and HEL1OS Observations side by side, each keeping its own conventions.

    Every distinguishing fact survives: instrument identity, unit, and quantity name. If any
    collapsed, a rate would be summed with a count and nothing downstream would notice.
    """
    solexs_path = sfx.write_lc(sfx.sdd2(tmp_path) / "s.lc", rows=86_400)
    solexs = solexs_lc.parse(solexs_path, Digest(digest_file(solexs_path).hex))
    solexs_rows = [
        o for i, o in enumerate(solexs.observations(
            source_id=Identifier("issdc-pradan"), ingest_time=None)) if i < 50
    ]

    hel1os_path = fx.write_lightcurve(tmp_path / "lightcurve_czt1.fits", rows=10)
    hel1os = lc.parse(hel1os_path, Digest(digest_file(hel1os_path).hex), detector="czt1")
    hel1os_rows = list(hel1os.observations(
        source_id=Identifier("issdc-pradan"), ingest_time=None))

    both: list[Observation] = solexs_rows + hel1os_rows
    validator = validator_for("observation")
    for observation in both:
        validator.validate(observation.to_dict())

    instruments = {str(o.instrument_id) for o in both}
    assert instruments == {"solexs-sdd2", "hel1os-czt1"}

    # The unit distinguishes them, and the two are never the same string.
    assert {o.unit for o in solexs_rows} == {"counts"}
    assert {o.unit for o in hel1os_rows} == {"cts/s"}
    assert not ({o.unit for o in solexs_rows} & {o.unit for o in hel1os_rows})

    # And so does the quantity: HEL1OS carries its band, SoLEXS carries none.
    assert {o.quantity for o in solexs_rows} == {"counts"}
    assert all(o.quantity.startswith("count_rate_") for o in hel1os_rows)


def test_the_three_channel_spaces_never_merge(tmp_path):
    """F-11: SoLEXS PI(340), CZT PHA(341), CdTe PHA(511).

    Three spaces, three modules, three separately-validated declarations. Stacking any two
    would fabricate a channel correspondence that does not exist.
    """
    czt = spectra.parse(fx.write_spectra(tmp_path / "czt.fits", detector="czt1"),
                        Digest("a" * 64), detector="czt1")
    cdte = spectra.parse(fx.write_spectra(tmp_path / "cdte.fits", detector="cdte1"),
                         Digest("b" * 64), detector="cdte1")
    solexs = solexs_pi.parse(
        sfx.write_pi(sfx.sdd2(tmp_path) / "s.pi", rows=86_400), Digest("c" * 64))

    assert len(czt.channel_map) == 341
    assert len(cdte.channel_map) == 511
    assert len(solexs.channel_map) == 340
    assert len({len(czt.channel_map), len(cdte.channel_map), len(solexs.channel_map)}) == 3

    # PI is not PHA, and the two modules say so independently.
    assert solexs.header.chantype == "PI"
    assert czt.header.chantype == "PHA" == cdte.header.chantype


def test_the_two_time_encodings_do_not_cross(tmp_path):
    """SoLEXS states Unix seconds; HEL1OS states MJD. Both resolve to the same UTC.

    Reading one with the other's epoch is a ~49-year error of the kind F-05 exists for, so
    each parser converts with its own declared encoding and the results are compared as
    instants rather than as numbers.
    """
    solexs_instant = solexs_lc.unix_to_timestamp(1_715_644_800.0)
    hel1os_instant = lc.mjd_to_timestamp(fx.TSTART_MJD)

    assert str(solexs_instant) == "2024-05-14T00:00:00Z"
    assert str(hel1os_instant).startswith("2025-12-08T00:00:08")
    assert solexs_lc.MJDREFI_UNIX == 40587
    assert lc.MJD_UNIX_EPOCH == 40587.0

    # The same instant expressed both ways agrees.
    unix_of_mjd = (fx.TSTART_MJD - 40587.0) * 86_400.0
    assert lc.mjd_to_timestamp(fx.TSTART_MJD) == solexs_lc.unix_to_timestamp(unix_of_mjd)


# ═══════════════════════════════════════════ the real corpus


@real_only
def test_the_version_distribution_matches_the_specification():
    """§4 `OBSERVED`: V111 ×371, V211 ×16, V112 ×3, V311 ×1 across 391 orbits."""
    counts: dict[int, int] = {}
    stems = []
    for path in HEL1OS_ROOT.iterdir():
        if not path.is_dir() or path.name.startswith("._"):
            continue
        parsed = orbit.parse_stem(path.name)
        stems.append(parsed)
        counts[parsed.version] = counts.get(parsed.version, 0) + 1

    assert len(stems) == 391
    assert counts == {111: 371, 211: 16, 112: 3, 311: 1}


@real_only
def test_both_overlap_classes_exist_and_resolve():
    """§4's Class A and Class B, both present in the archive.

    Class A resolves by precedence at file level. Class B is *detected* here and resolved by
    the minute-level coverage map, which §4 ties to emitting T3/T4/T5 — #19's work.
    """
    a1 = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V111")
    a2 = orbit.parse_stem("HLS_20251208_000008_43178sec_lev1_V211")
    assert (HEL1OS_ROOT / a1.stem).is_dir() and (HEL1OS_ROOT / a2.stem).is_dir()
    assert orbit.overlaps(a1, a2)
    assert orbit.precedence(a1, a2) is a2

    b1 = orbit.parse_stem("HLS_20251207_120003_43195sec_lev1_V211")
    b2 = orbit.parse_stem("HLS_20251207_121028_42570sec_lev1_V111")
    assert (HEL1OS_ROOT / b1.stem).is_dir() and (HEL1OS_ROOT / b2.stem).is_dir()
    assert orbit.overlaps(b1, b2)
    assert b1.start_epoch != b2.start_epoch and b1.duration_s != b2.duration_s


@real_only
def test_the_real_band_lightcurves_carry_the_specified_bands():
    """§2.6 `OBSERVED`, re-measured: five bands per detector, edges from EXTNAME."""
    for detector, expected in (("czt1", fx.CZT_BANDS), ("cdte1", fx.CDTE_BANDS)):
        family = "czt" if detector.startswith("czt") else "cdte"
        path = orbit_dir() / family / f"lightcurve_{detector}.fits"
        product = lc.parse(path, Digest(digest_file(path).hex), detector=detector)

        assert [(b.low_kev, b.high_kev) for b in product.bands] == list(expected)
        assert sum(1 for b in product.bands if b.is_total) == 1

        # §2.6 states `NAXIS2 ≈ 43171` — approximate, and the archive shows why the word
        # matters. Measured on this orbit:
        #     CZT1   43171, 43171, 43171, 43171, 43171   — one shared axis
        #     CdTe1  43154, 43171, 43163, 43133, 43171   — FIVE DIFFERENT LENGTHS
        # So the bands of one CdTe detector do NOT share a time axis. §2.6 neither states
        # nor denies this; the parser keeps each band's own MJD column, which is the only
        # reading that survives the measurement. Recorded as CONTRA-007 Observation D.
        for band in product.bands:
            assert 43_000 <= len(band.mjd) <= 43_200, (
                f"{detector} {band.extname}: {len(band.mjd)} samples")
            assert len(band.mjd) == len(band.rate) == len(band.stat_err), (
                f"{detector} {band.extname}: columns of unequal length")


@real_only
def test_cdte_bands_do_not_share_a_time_axis():
    """CONTRA-007 Observation D, asserted rather than assumed.

    A consumer building a per-detector band × time array would silently misalign up to 38
    samples if it assumed one axis. The parser gives each band its own, and this pins the
    property so a future change to either the archive or the parser is visible.
    """
    path = orbit_dir() / "cdte" / "lightcurve_cdte1.fits"
    product = lc.parse(path, Digest(digest_file(path).hex), detector="cdte1")
    lengths = {band.extname: len(band.mjd) for band in product.bands}
    assert len(set(lengths.values())) > 1, lengths

    czt_path = orbit_dir() / "czt" / "lightcurve_czt1.fits"
    czt = lc.parse(czt_path, Digest(digest_file(czt_path).hex), detector="czt1")
    assert len({len(band.mjd) for band in czt.bands}) == 1


@real_only
def test_the_real_spectra_resolve_to_h3_with_both_channel_spaces():
    """§2.7 `OBSERVED`: 341 for CZT, 511 for CdTe, 2157 rows, epoch H3."""
    for detector, detchans in (("czt1", 341), ("cdte1", 511)):
        family = "czt" if detector.startswith("czt") else "cdte"
        path = orbit_dir() / family / f"hel1os_{family}_spectra_{detector}.fits"
        product = spectra.parse(path, Digest(digest_file(path).hex), detector=detector)

        assert product.header.detchans == detchans
        assert product.header.chantype == "PHA"
        assert product.header.hduclas3 == "COUNT"
        assert product.header.rows == 2157
        assert product.epoch.hypothesis == "H3"
        assert product.epoch.exposure_s == 20.0

        first = next(iter(product.spectra()))
        assert len(first.counts) == detchans


@real_only
def test_the_real_housekeeping_reproduces_the_recorded_inversion_statistics():
    """§2.8 `OBSERVED`: 9,514 rows; 424 of 9,513 steps decrease; max backward 892.4 ms;
    0 duplicates; range within the header span.

    Every figure re-measured. §2.8 reports these and defines no threshold, so the assertions
    are on the measurements themselves rather than on any tolerance.
    """
    path = orbit_dir() / "aux" / "hk.fits"
    product = hk.parse(path, Digest(digest_file(path).hex))
    stats = product.inversions

    assert stats.rows == 9_514
    assert stats.steps == 9_513
    assert stats.n_out_of_order == 424
    assert round(stats.max_backward_step_ms, 1) == 892.4
    assert len(set(product.mjd)) == len(product.mjd)
    assert product.header_tstart <= min(product.mjd)
    assert max(product.mjd) <= product.header_tstop


@real_only
def test_the_real_housekeeping_is_not_sorted():
    """§2.8 r4, binding: the parser preserves archive order exactly and performs no sorting.

    424 inversions survive, which is the observable proof that nothing reordered them.
    """
    path = orbit_dir() / "aux" / "hk.fits"
    product = hk.parse(path, Digest(digest_file(path).hex))
    assert list(product.mjd) != sorted(product.mjd)
    assert product.inversions.n_out_of_order == 424


@real_only
def test_the_real_gti_products_use_lowercase_columns():
    """§2.9 / §8 A-2: lowercase `tstart`/`tstop`, unlike SoLEXS's uppercase."""
    for detector in ("czt1", "czt2", "cdte1", "cdte2"):
        path = orbit_dir() / "aux" / f"gti{detector}.fits"
        product = gti.parse(path, Digest(digest_file(path).hex), detector=detector)
        assert product.detector_active
        assert len(product.intervals) == 1
        assert product.live_time_s > 43_000


@real_only
def test_the_real_event_list_has_all_four_detectors():
    """§2.5 `OBSERVED`: four detector HDUs, 1.3–1.6 M rows each, `ener` in keV."""
    path = orbit_dir() / "events" / "evt.fits"
    product = events.parse(path, Digest(digest_file(path).hex))

    assert {d.detector for d in product.detectors} == {"czt1", "czt2", "cdte1", "cdte2"}
    for detector in product.detectors:
        assert 1_300_000 <= detector.rows <= 1_600_000

    first = next(iter(product.events("czt1")))
    assert first.energy_kev > 0
    assert str(first.valid_time).startswith("2025-12-08T")

    # §2.5: exposed, and deliberately not ingestible into the canonical tables.
    assert not hasattr(product, "observations")


@real_only
@solexs_only
def test_both_real_instruments_coexist_without_leakage():
    """The coexistence claim, on real data from both instruments.

    SoLEXS 2024-05-14 (Unix seconds, PI 340, counts) and HEL1OS 2025-12-08 (MJD, PHA 341,
    cts/s) parsed by separate modules into one collection, with every distinguishing fact
    intact and no shared convention anywhere.
    """
    solexs_path = (SOLEXS_ROOT / "AL1_SLX_L1_20240514_v1.0" / "AL1_SLX_L1_20240514_v1.0"
                   / "SDD2" / "AL1_SOLEXS_20240514_SDD2_L1.lc.gz")
    solexs = solexs_lc.parse(solexs_path, Digest(digest_file(solexs_path).hex))

    hel1os_path = orbit_dir() / "czt" / "lightcurve_czt1.fits"
    hel1os = lc.parse(hel1os_path, Digest(digest_file(hel1os_path).hex), detector="czt1")

    solexs_rows = [
        o for i, o in enumerate(solexs.observations(
            source_id=Identifier("issdc-pradan"), ingest_time=None)) if i < 20
    ]
    hel1os_rows = []
    for observation in hel1os.observations(source_id=Identifier("issdc-pradan"),
                                           ingest_time=None):
        hel1os_rows.append(observation)
        if len(hel1os_rows) == 20:
            break

    validator = validator_for("observation")
    for observation in solexs_rows + hel1os_rows:
        validator.validate(observation.to_dict())

    assert {str(o.instrument_id) for o in solexs_rows} == {"solexs-sdd2"}
    assert {str(o.instrument_id) for o in hel1os_rows} == {"hel1os-czt1"}
    assert {o.unit for o in solexs_rows} == {"counts"}
    assert {o.unit for o in hel1os_rows} == {"cts/s"}

    # Different missions, different years, different digests — nothing shared but the schema.
    assert str(solexs_rows[0].valid_time).startswith("2024-05-14")
    assert str(hel1os_rows[0].valid_time).startswith("2025-12-08")
    assert solexs_rows[0].source_digest != hel1os_rows[0].source_digest

@real_only
def test_the_real_housekeeping_carries_every_decisive_column_with_its_unit():
    """§2.8's decisive columns on the reference orbit, with the units the archive declares.

    The detector-health columns exist only with a detector prefix (`czt1hotpixcnt`), which is
    how §3 T4 names them and how §2.8's abbreviation resolves — recorded as CONTRA-007
    Observation E rather than inferred silently.
    """
    path = orbit_dir() / "aux" / "hk.fits"
    product = hk.parse(path, Digest(digest_file(path).hex))

    for name in hk.CAPTURED:
        assert name in product.columns, name
    assert product.units["czthvmon"] == "V"
    assert product.units["cdtehvmon"] == "V"
    assert product.units["czt1enth"] == "keV"
    assert {product.units[name] for name in hk.THERMAL} == {"degC"}
    assert {product.units[name] for name in hk.RATES} == {"c/s"}

    # §8 A-4: czt2enth declares no unit in the archive, so czt1enth's is applied and recorded.
    assert product.units["czt2enth"] == "keV"
    assert any("czt2enth" in assumption for assumption in product.assumptions)
    assert isinstance(product.columns["czt1hotpixcnt"][0], int)


@real_only
def test_real_event_rows_pass_the_r7_rules_until_the_archive_falsifies_section_2_5():
    """The §2.5 row rules on real events, and the falsification they run into.

    Every row the archive yields here satisfies r7's span check and V-EVT-2 — `utc-isot` agrees
    with `mjd` to the millisecond it carries. The stream then terminates at F-16 because `mjd`
    steps backward, which §2.5 forbids and the archive does anyway: CONTRA-008, OPEN. The rule
    is enforced as written, so this test pins the falsification rather than hiding it.
    """
    path = orbit_dir() / "events" / "evt.fits"
    product = events.parse(path, Digest(digest_file(path).hex))

    seen = 0
    with pytest.raises(ContractViolation) as caught:
        for event in product.events("czt1"):
            seen += 1
            assert event.energy_kev > 0
            assert event.pixel is not None
    assert seen > 0
    assert caught.value.message.startswith("F-16")
    assert "CONTRA-008" in caught.value.message

