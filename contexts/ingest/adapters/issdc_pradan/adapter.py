"""The ISSDC-PRADAN channel: Aditya-L1 SoLEXS daily archives.

WHAT ACQUISITION ACTUALLY MEANS FOR THIS CHANNEL
------------------------------------------------
PRADAN is not an API. ISSDC's own published download script states the procedure: *"Login to
Pradan in your browser, select data of your interest and download script for the session"*,
and warns that *"There are session download limits, request rate limit and session timeouts
in place... Violations may lead to blocking."* The session is an interactive browser login
producing short-lived cookies, and the archive arrives ~33 days after the observations it
contains.

So the network step is performed by a person, outside this system, and what it leaves behind
is an extracted archive tree. This adapter's `acquire` is the step that brings that tree into
the platform: it locates the day's archive, has the kernel digest every product in it, stamps
the moment the system learned of it, and returns provenance for all of it.

That is not a reduced form of acquisition — it is the acquisition boundary this mission
actually has. ADR-0023 already describes the resulting tree correctly: Tier 0, referenced
rather than stored, a local copy that is an evictable cache and never the system of record.

**No HTTP is performed here, and none is simulated.** Writing a fetch against a portal that
requires an interactive login would mean inventing a transport this channel does not have,
and inventing responses to go with it. When the day's products are not on disk, the adapter
raises `UnavailableResource` — which is the true statement (the data has not been retrieved)
rather than a fabricated one.

THIS ADAPTER HOLDS NO CREDENTIAL
--------------------------------
It cannot leak a secret because it has none: authentication happens in a browser, before and
outside this code. Its descriptor records `requires_credentials=True` because *re-acquiring*
from PRADAN needs a session, which is what a future reader must know (ADR-0023). That is the
whole of what crosses. `test_the_adapter_holds_no_credential` asserts the absence, which is
a stronger form of STD-19 than confinement: there is nothing here to confine.

ARCHIVE LAYOUT
--------------
Per `SPEC-parsers@r6` §1.1, verified against the archive on disk (436 archives, 436 unique
dates, 431 at v1.0 and 5 at v1.1):

    AL1_SLX_L1_<YYYYMMDD>_v<1.0|1.1>/        outer stem
    └── AL1_SLX_L1_<YYYYMMDD>_v<VER>/        the stem repeats inside
        ├── SDD1/ AL1_SOLEXS_<date>_SDD1_L1.gti.gz
        └── SDD2/ AL1_SOLEXS_<date>_SDD2_L1.{gti,lc,pi}.gz
            [v1.1 only] ...hk.gz and a quicklook PNG

This adapter reads the layout and reports what it finds. It does not parse a product — the
SoLEXS parsers are M3/E5/#17 and the HEL1OS parsers are #18.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from contexts.ingest import boundary
from contexts.ingest.acquisition import Acquisition, AcquisitionProvenance, RawArtifact
from contexts.ingest.descriptor import (
    LatencyClass,
    RetrievalDescriptor,
    SourceDescriptor,
)
from contexts.ingest.errors import UnavailableResource
from domain.errors import ContractViolation
from domain.values import Digest, Identifier, RunId
from kernel.provenance import ProvenanceStore, begin_run, digest_chunks, digest_file

#: This channel's identity, as E5 §18's acceptance criterion names it.
SOURCE_ID = "issdc-pradan"
AUTHORITY = "ISSDC, Indian Space Research Organisation"

#: ~33 days. Not a target and not a measurement of a service — a characterisation of a manual
#: archive process, which is why it is approximate. ADR-0001 makes real-time Aditya-L1
#: services a binding non-goal *while the archive remains ~33 days latent*, and this is the
#: value that statement refers to.
LATENCY = "~33d"
GRANULARITY = "daily-archive"

#: The portal a future reader would return to. Contains no token and no session state; the
#: cookies ISSDC issues are per-session and per-person, and recording one would violate
#: STD-19 and be useless within the hour besides.
PORTAL = "https://pradan1.issdc.gov.in/al1/"

#: `AL1_SLX_L1_20240514_v1.0`
ARCHIVE_STEM = re.compile(r"^AL1_SLX_L1_(\d{8})_v(\d+\.\d+)$")
SELECTOR = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")

#: Science products. The v1.1 quicklook PNG is deliberately excluded: it is a rendering of
#: the data, not the data, and including it would make the archive digest depend on whether
#: a preview image happened to be generated.
PRODUCT_SUFFIX = ".gz"


@dataclass(frozen=True)
class ArchiveProduct:
    """One file inside a daily archive, with the digest the kernel minted for it."""

    #: Path relative to the archive's outer stem, so the identity does not depend on where
    #: the cache happens to sit.
    relative_path: str
    digest: Digest
    size_bytes: int


class IssdcPradanAdapter:
    """The Aditya-L1 SoLEXS daily archive channel.

    Satisfies `contexts.ingest.SourceAdapter` structurally — it inherits nothing. The
    conformance check `verify_conformance` is what decides whether it may feed the platform.
    """

    def __init__(self, archive_root: Path, store: ProvenanceStore) -> None:
        """`archive_root` is the directory holding the extracted daily archives.

        Passed in rather than discovered. A path constant would make the adapter untestable
        without the 3.5 GB corpus and would hard-code one machine's layout into the platform;
        ADR-0023 makes the local copy a cache whose location is not the system's business.
        """
        self.archive_root = Path(archive_root)
        self._store = store

    # ── what this channel is ────────────────────────────────────────────────────

    def descriptor(self) -> SourceDescriptor:
        """E5 §18's acceptance criterion, as data.

        Constant for the life of the adapter — it depends on nothing but the constants above,
        so it cannot vary between calls, which `verify_descriptor` checks.
        """
        return SourceDescriptor(
            source_id=Identifier(SOURCE_ID),
            authority=AUTHORITY,
            latency_class=LatencyClass(LATENCY),
            granularity=Identifier(GRANULARITY),
            retrieval=RetrievalDescriptor(
                provider="ISSDC PRADAN",
                locator=f"{PORTAL} :: AL1_SLX_L1_<YYYYMMDD>_v<VER>",
                requires_credentials=True,
            ),
        )

    # ── locating a day ──────────────────────────────────────────────────────────

    def archive_for(self, selector: str) -> Path:
        """The outer stem directory for a date, or `UnavailableResource` if it is not here.

        Refuses a malformed selector with `ContractViolation` rather than searching for
        something that could not exist: a selector the channel cannot interpret is a caller
        error, not an unavailable resource, and conflating the two would send someone looking
        for a network problem they do not have.
        """
        match = SELECTOR.match(selector) if isinstance(selector, str) else None
        if match is None:
            raise ContractViolation(
                "/selector",
                f"selector {selector!r} is not a date of the form YYYY-MM-DD. This channel's "
                f"granularity is {GRANULARITY!r}, so a day is what it can be asked for.",
            )
        compact = "".join(match.groups())

        if not self.archive_root.is_dir():
            raise UnavailableResource(
                f"the SoLEXS archive root {self.archive_root} is not present. PRADAN "
                f"retrieval is a manual browser session performed outside this system; "
                f"nothing here can fetch it."
            )

        candidates = sorted(
            path
            for path in self.archive_root.iterdir()
            if path.is_dir()
            and not path.name.startswith("._")
            and (m := ARCHIVE_STEM.match(path.name)) is not None
            and m.group(1) == compact
        )
        if not candidates:
            raise UnavailableResource(
                f"no SoLEXS archive for {selector} under {self.archive_root}. The day has "
                f"not been retrieved from PRADAN."
            )
        if len(candidates) > 1:
            # SPEC-parsers r6 records 436 archives across 436 unique dates, so this does not
            # occur in the corpus. If it ever does, two versions of one day is a question
            # about which is authoritative, and guessing would silently pick one.
            raise ContractViolation(
                "/selector",
                f"{selector} has {len(candidates)} archives "
                f"({[p.name for p in candidates]}). SPEC-parsers r6 records no date with two "
                f"version variants; which is authoritative is not this adapter's to decide.",
            )
        return candidates[0]

    def version_of(self, archive: Path) -> str:
        match = ARCHIVE_STEM.match(archive.name)
        if match is None:
            raise ContractViolation(
                "/archive", f"{archive.name!r} is not an AL1_SLX_L1 archive stem"
            )
        return match.group(2)

    def products(self, selector: str) -> tuple[ArchiveProduct, ...]:
        """Every science product in the day's archive, digested by the kernel, sorted.

        Sorted by relative path so the sequence is deterministic: the archive digest below is
        computed over it, and a filesystem-ordering difference between two machines would
        otherwise produce two identities for the same bytes.

        AppleDouble sidecars (`._*`) are excluded. They are created by macOS on non-native
        filesystems, are not part of the archive ISSDC published, and their presence differs
        between the machine that downloaded the data and any other — including them would
        make the digest depend on which computer looked at it.
        """
        archive = self.archive_for(selector)
        found: list[ArchiveProduct] = []
        for path in sorted(archive.rglob(f"*{PRODUCT_SUFFIX}")):
            if path.name.startswith("._") or not path.is_file():
                continue
            found.append(
                ArchiveProduct(
                    relative_path=path.relative_to(archive).as_posix(),
                    digest=Digest(digest_file(path).hex),
                    size_bytes=path.stat().st_size,
                )
            )
        if not found:
            raise UnavailableResource(
                f"the archive directory for {selector} exists at {archive} but contains no "
                f"{PRODUCT_SUFFIX} products. The five v1.1 archives carry a tracked quicklook "
                f"PNG, so the directory is present in a clean checkout while the science "
                f"products are not — this is the condition STD-12 and E5 §16 require be "
                f"detected by testing for the products themselves."
            )
        return tuple(found)

    # ── acquiring ───────────────────────────────────────────────────────────────

    def manifest_bytes(self, products: tuple[ArchiveProduct, ...]) -> bytes:
        """The canonical listing whose digest identifies the daily archive.

        One line per product: digest, size, relative path. Sorted, so the same archive
        produces the same bytes on any machine.

        A rollup rather than a digest of a concatenation, for the reason `DatasetRelease`
        rolls per-table digests up to a release digest (ADR-0006): a changed byte anywhere
        changes the archive identity *and* stays locatable to the product it changed. A
        single digest over concatenated content would detect the change and lose its address.
        """
        lines = [
            f"{product.digest} {product.size_bytes} {product.relative_path}"
            for product in products
        ]
        return ("\n".join(lines) + "\n").encode()

    def acquire(self, selector: str) -> Acquisition:
        """Bring one day's archive into the platform (E5 §4).

        The order is TIS §16.1's, and each step is performed by whichever component owns it:

            1. locate the day             this adapter
            2. digest every product       the kernel — ADR-0005 permits nothing else to
            3. roll up to one identity    the kernel again, over the canonical listing
            4. register the listing       the kernel's store, so the identity is resolvable
            5. stamp ingest_time          the acquisition boundary — the one clock read
            6. return artifact + record   with the digest they both name

        No retry loop and no timeout. E5 §15 makes retry policy adapter-local, and this
        adapter performs no network call: there is nothing to retry, and adding a loop around
        a filesystem read would be inventing transport behaviour this channel does not have.
        """
        found = self.products(selector)
        archive = self.archive_for(selector)

        listing = self.manifest_bytes(found)
        archive_digest = Digest(digest_chunks([listing]).hex)

        # Register the listing itself, so the archive's identity resolves to bytes the store
        # holds. The products are NOT registered: they are Tier 0, referenced and never
        # redistributed (ADR-0023, STD-23, E5 §11(iv)).
        self._store.put_bytes(listing)

        run = begin_run(context="ingest", event="acquire")
        stamped = boundary.stamp()

        return Acquisition(
            artifact=RawArtifact(
                digest=archive_digest,
                size_bytes=sum(product.size_bytes for product in found),
                retrieval=self.descriptor().retrieval,
                cache_path=archive,
            ),
            provenance=AcquisitionProvenance(
                run_id=RunId(run.run_id),
                source_id=Identifier(SOURCE_ID),
                artifact_digest=archive_digest,
                ingest_time=stamped,
                instruments=(Identifier("solexs"),),
            ),
        )


__all__ = [
    "AUTHORITY",
    "ARCHIVE_STEM",
    "ArchiveProduct",
    "GRANULARITY",
    "IssdcPradanAdapter",
    "LATENCY",
    "PORTAL",
    "SOURCE_ID",
]
