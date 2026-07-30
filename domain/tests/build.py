"""Literal constructors for the test suites.

NOT FIXTURES, AND THE DISTINCTION MATTERS (TIS E4 §16)
------------------------------------------------------
E4 forbids fixtures and mocks: "if a mock is needed the code is in the wrong layer". These are
neither. Each function returns a fully-constructed real entity built from literals, with
keyword overrides so that every test states exactly the field it is varying and inherits
nothing implicit. There is no setup, no teardown, no shared mutable state, and no test doubles
— nothing here stands in for a collaborator, because the domain has none.

They exist so that a test about `ingest_time` is one line about `ingest_time` rather than
twelve lines of unrelated valid fields, which is what makes the varying field visible.
"""

from __future__ import annotations

from domain.entities import (
    Blas,
    Dataset,
    DatasetRelease,
    EnvironmentRelease,
    Evaluation,
    EvidenceBinding,
    Instrument,
    LabelRelease,
    LabelSource,
    Method,
    MethodRelease,
    Observation,
    Platform,
    Protocol,
    Source,
    Splits,
    Supersession,
    Table,
)
from domain.values import (
    Digest,
    Identifier,
    Interval,
    ReproductionClass,
    RunId,
    Score,
    Severity,
    SplitStrategy,
    Timestamp,
)

RUN = "01ARZ3NDEKTSV4RRFFQ69G5FAV"


def digest(seed: str = "a") -> Digest:
    """A well-formed digest from a single repeated character.

    Not computed from anything: ADR-0005 reserves minting to the kernel, and a test that
    hashed its own bytes here would be exercising a capability the domain must not have.
    """
    return Digest(seed * 64)


def observation(**overrides) -> Observation:
    fields = {
        "source_id": Identifier("issdc"),
        "instrument_id": Identifier("solexs"),
        "quantity": "count_rate",
        "unit": "counts/s",
        "valid_time": Timestamp("2024-03-01T00:00:00Z"),
        "ingest_time": Timestamp("2024-04-03T12:00:00Z"),
        "value": 12.5,
        "source_digest": digest("a"),
    }
    fields.update(overrides)
    return Observation(**fields)


def interval(**overrides) -> Interval:
    fields = {
        "lower": 0.80,
        "upper": 0.90,
        "level": 0.95,
        "estimator": "bootstrap",
        "exchangeable_unit": "event",
    }
    fields.update(overrides)
    return Interval(**fields)


def score(**overrides) -> Score:
    fields = {
        "metric": "tss",
        "value": 0.85,
        "interval": interval(),
        "denominator": 192541,
    }
    fields.update(overrides)
    return Score(**fields)


def table(**overrides) -> Table:
    fields = {
        "key": "T1",
        "name": "solexs_lightcurve",
        "digest": digest("c"),
        "n_files": 1985,
        "bytes": 600_000_000,
    }
    fields.update(overrides)
    return Table(**fields)


def dataset_release(**overrides) -> DatasetRelease:
    fields = {
        "dataset_id": Identifier("adityanet-v2"),
        "version": "r1",
        "digest": digest("b"),
        "tables": (table(),),
        "frozen_at": Timestamp("2024-05-01T00:00:00Z"),
        "n_files": 1985,
        "total_bytes": 600_000_000,
        "doi": None,
    }
    fields.update(overrides)
    return DatasetRelease(**fields)


def label_release(**overrides) -> LabelRelease:
    fields = {
        "label_source_id": Identifier("goes-flare-catalog"),
        "authority": "NOAA SWPC",
        "digest": digest("d"),
        "ingest_time": Timestamp("2024-05-01T00:00:00Z"),
        "n_events": 431,
        "supersedes_digest": None,
    }
    fields.update(overrides)
    return LabelRelease(**fields)


def method_release(**overrides) -> MethodRelease:
    fields = {
        "method_id": Identifier("threshold-detector"),
        "digest": digest("e"),
        "artifact_digest": digest("f"),
        "declared_instruments": (Identifier("solexs"),),
        "parameters": {"threshold": 3.2},
        "training_provenance": None,
    }
    fields.update(overrides)
    return MethodRelease(**fields)


def environment_release(**overrides) -> EnvironmentRelease:
    fields = {
        "digest": digest("0"),
        "interpreter_version": "3.12.3",
        "lockfile_digest": digest("1"),
        "blas": Blas("OpenBLAS", "0.3.26"),
        "thread_counts": {"OMP_NUM_THREADS": 1},
        "hash_seed": 0,
        "platform": Platform("linux", "x86_64"),
        "container_digest": None,
    }
    fields.update(overrides)
    return EnvironmentRelease(**fields)


def splits(**overrides) -> Splits:
    fields = {
        "strategy": SplitStrategy.CHRONOLOGICAL,
        "test_start": Timestamp("2024-04-01T00:00:00Z"),
        "val_fraction": None,
    }
    fields.update(overrides)
    return Splits(**fields)


def protocol(**overrides) -> Protocol:
    fields = {
        "protocol_id": Identifier("detection-v1"),
        "digest": digest("2"),
        "task": "flare detection",
        "splits": splits(),
        "metrics": ("tss",),
        "uncertainty_estimator": "bootstrap",
        "exchangeable_unit": "event",
        "permitted_instruments": (Identifier("solexs"),),
        "label_source_id": Identifier("goes-flare-catalog"),
        "requires_bitemporal": False,
        "tolerance": 0.0,
        "operating_points": (),
    }
    fields.update(overrides)
    return Protocol(**fields)


def evaluation(**overrides) -> Evaluation:
    fields = {
        "digest": digest("3"),
        "method_release": digest("e"),
        "dataset_release": digest("b"),
        "label_release": digest("d"),
        "protocol": digest("2"),
        "environment_release": digest("0"),
        "reproduction_class": ReproductionClass.EXACT,
        "leakage_gate_applied": False,
        "scores": (score(),),
    }
    fields.update(overrides)
    return Evaluation(**fields)


def evidence_binding(**overrides) -> EvidenceBinding:
    fields = {
        "claim_id": "tss-headline",
        "measurement_key": "detection.tss",
        "artifact": "artifacts/v2/evaluation.json",
        "pointer": "/scores/0/value",
        "artifact_digest": digest("4"),
        "run_id": RunId(RUN),
    }
    fields.update(overrides)
    return EvidenceBinding(**fields)


def supersession(**overrides) -> Supersession:
    fields = {
        "superseded": digest("b"),
        "superseding": digest("5"),
        "severity": Severity.CORRECTION,
        "reason": "parser defect in the SoLEXS lightcurve reader",
        "effective_date": Timestamp("2024-06-01T00:00:00Z"),
        "discovered_by": RunId(RUN),
    }
    fields.update(overrides)
    return Supersession(**fields)


def named_entities() -> tuple[object, ...]:
    """One instance of each entity permitted a mutable identity (TIS E4 §11(ii))."""
    return (
        Dataset(Identifier("adityanet-v2"), "AdityaNet v2"),
        Method(Identifier("threshold-detector"), "Count-rate threshold"),
        Source(Identifier("issdc"), "ISSDC PRADAN"),
        Instrument(Identifier("solexs"), "SoLEXS"),
        LabelSource(Identifier("goes-flare-catalog"), "NOAA GOES flare catalog"),
    )
