"""Ingest — acquire from a Source, and canonicalise via an Instrument parser.

M3/E5/#15 delivers the **contract** half of this context: what an acquisition channel must
provide, what it may never let out, and where the one sanctioned clock read lives. It delivers
no channel. The ISSDC-PRADAN adapter is #16; the SoLEXS and HEL1OS parsers are #17 and #18;
the bitemporal write path is #19.

Public interface (E5 §4):

    SourceAdapter            the protocol a channel satisfies
    verify_conformance       what an adapter must pass before its data enters the platform
    SourceDescriptor         source_id · authority · latency_class · granularity · retrieval
    RawArtifact              a Tier 0 artifact, identified rather than held
    AcquisitionProvenance    who fetched what, from where, and when the system learned it
    Acquisition              the two together, which is what `acquire` returns
    boundary.stamp           the single sanctioned clock read (ADR-0004, TIS §0.4)
    Credential               a secret that cannot be printed or serialised (STD-19)
    assert_credential_free   refuse to let one cross the boundary

THE THREE RULES THIS CONTEXT EXISTS TO KEEP
--------------------------------------------
**Credentials never leave.** E5 §13 makes this the highest-sensitivity context — it holds the
only secrets in the system. `Credential` redacts itself in `repr`, `str` and `format`, so the
common leak routes are closed by the type; `assert_credential_free` closes the rest by walking
anything about to cross outward.

**Tier 0 bytes are never redistributed.** `RawArtifact` has a digest, a size, a way to
re-acquire, and no field that could hold the bytes. ADR-0023 and E5 §12 both land here.

**Both times, and the second one never fabricated.** `ingest_time` is stamped at this
boundary and nowhere else (ADR-0004). Nothing here supplies one for a historical row —
ADR-0022 gives `null` exactly one meaning, and E5 §11(ii) forbids any code path from writing
a non-null value for data that predates bitemporal capture.

IMPORTS. `contracts`, `domain`, `kernel` and the standard library — exactly what
`contexts.ingest`'s policy grants (ADR-0026, enforced by M2/E4/#13). No other context.
"""

from contexts.ingest.acquisition import (
    Acquisition,
    AcquisitionProvenance,
    RawArtifact,
)
from contexts.ingest.contract import (
    CONFORMANCE_GATE,
    SourceAdapter,
    verify_acquisition,
    verify_conformance,
    verify_descriptor,
)
from contexts.ingest.credentials import (
    CREDENTIAL_BOUNDARY,
    Credential,
    assert_credential_free,
)
from contexts.ingest.descriptor import (
    LatencyClass,
    RetrievalDescriptor,
    SourceDescriptor,
)
from contexts.ingest.errors import (
    ContractViolation,
    IngestError,
    IntegrityFailure,
    PolicyRejection,
    UnavailableResource,
)

__all__ = [
    "Acquisition",
    "AcquisitionProvenance",
    "CONFORMANCE_GATE",
    "CREDENTIAL_BOUNDARY",
    "ContractViolation",
    "Credential",
    "IngestError",
    "IntegrityFailure",
    "LatencyClass",
    "PolicyRejection",
    "RawArtifact",
    "RetrievalDescriptor",
    "SourceAdapter",
    "SourceDescriptor",
    "UnavailableResource",
    "assert_credential_free",
    "verify_acquisition",
    "verify_conformance",
    "verify_descriptor",
]
