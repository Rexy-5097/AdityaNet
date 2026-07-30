"""The credential boundary — the one thing this context must never leak.

E5 §13 calls Ingest the highest-sensitivity context: it holds the only secrets in the system.
STD-19 states the rule, and E5 §11(iii) states it as an invariant:

    Secrets exist only within the Ingest context's source adapters. They are never logged,
    never persisted to an artifact, and never cross a context boundary.

A rule of that shape is normally enforced by discipline, and discipline fails silently — the
leak is a log line nobody reads until someone else does. So it is enforced here in three ways
that do not depend on anyone remembering:

  1. `Credential` cannot be printed. `repr` and `str` return a redaction, so a secret cannot
     reach a log through the single most common route: an f-string, a `print`, or a traceback
     that includes local variables.
  2. `Credential` cannot be serialised. It has no `to_dict`, and `json.dumps` refuses it
     because it is not a JSON type. An artifact cannot silently acquire one.
  3. `assert_credential_free` inspects any object about to cross the boundary and refuses it
     if a `Credential` is reachable from it, at any depth.

Reading the secret requires calling `reveal()` explicitly. That is deliberate: an adapter
genuinely needs the value to authenticate, and making the read a named, greppable call means
`grep -rn 'reveal()' contexts/` enumerates every place a secret is touched — which is a
shorter list than every place a string is used.

WHAT THIS DOES NOT DO. It does not manage, store, rotate or fetch credentials. There is no
credential store, no provider abstraction and no configuration layer: ADR-0003 forbids a
configurable adapter framework until a second source exists, and ADR-0025 classifies exactly
that as a paid abstraction. Obtaining the secret is the adapter's business (M3/E5/#16).
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass

from contexts.ingest.errors import PolicyRejection

#: The gate named in a `PolicyRejection` raised from here. One string, so a caller matching
#: on it and a test asserting it cannot drift apart.
CREDENTIAL_BOUNDARY = "credential-boundary"

REDACTED = "<redacted>"

#: Field names that would carry a secret in plain form. Used only to catch a raw string that
#: was never wrapped in `Credential` — the wrapped case is caught by type, which is exact.
#: This list is a backstop for the mistake of not using the type at all, and is deliberately
#: about names rather than values: a heuristic over values would have to guess what a secret
#: looks like, and would be both wrong and unfalsifiable.
SECRET_FIELD_NAMES = frozenset({
    "credential", "credentials", "secret", "password", "passwd", "token",
    "api_key", "apikey", "access_key", "secret_key", "cookie", "cookies",
    "session", "session_id", "auth", "authorization", "bearer", "private_key",
})


@dataclass(frozen=True)
class Credential:
    """A secret held inside Ingest and nowhere else.

    Frozen, unprintable, unserialisable. The value is reachable only through `reveal()`.
    """

    #: What this secret is for, e.g. "issdc-pradan-session". Not itself secret — a purpose
    #: has to be nameable in a log for an operator to diagnose an authentication failure.
    purpose: str
    _value: str

    def __post_init__(self) -> None:
        if not isinstance(self.purpose, str) or not self.purpose:
            raise ValueError("a credential must state its purpose")
        if not isinstance(self._value, str) or not self._value:
            # An empty secret is almost always an unset environment variable read without
            # checking. Failing here turns a silent unauthenticated request into an abort.
            raise ValueError(f"credential {self.purpose!r} has no value")

    def reveal(self) -> str:
        """Return the secret. The only way to read it, and deliberately greppable."""
        return self._value

    def __repr__(self) -> str:
        return f"Credential(purpose={self.purpose!r}, value={REDACTED})"

    def __str__(self) -> str:
        return REDACTED

    def __format__(self, spec: str) -> str:
        # Without this, `f"{credential:>20}"` would bypass __str__ for some format specs.
        return REDACTED


def _reachable_credentials(value: object, trail: str, seen: set[int]) -> list[str]:
    """Every path within `value` at which a `Credential` or secret-named field is reachable.

    Walks dataclasses, mappings and sequences. Recursion is guarded by object identity so a
    cyclic structure terminates rather than exhausting the stack — a leak check that crashes
    is a leak check that gets removed.
    """
    if id(value) in seen:
        return []
    seen.add(id(value))

    if isinstance(value, Credential):
        return [trail or "/"]

    found: list[str] = []

    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            attribute = getattr(value, field.name, None)
            if field.name.strip("_").lower() in SECRET_FIELD_NAMES and isinstance(
                attribute, str
            ):
                found.append(f"{trail}/{field.name}")
            found += _reachable_credentials(attribute, f"{trail}/{field.name}", seen)
        return found

    if isinstance(value, dict):
        for key, item in value.items():
            here = f"{trail}/{key}"
            if isinstance(key, str) and key.strip("_").lower() in SECRET_FIELD_NAMES:
                found.append(here)
            found += _reachable_credentials(item, here, seen)
        return found

    if isinstance(value, (list, tuple, set, frozenset)):
        for index, item in enumerate(value):
            found += _reachable_credentials(item, f"{trail}/{index}", seen)
        return found

    return found


def assert_credential_free(value: object, *, what: str) -> None:
    """Refuse to let `value` cross the boundary if a secret is reachable from it.

    Applied to everything Ingest hands outward: the descriptor it publishes, the provenance
    it records, the artifact it produces. `what` names the thing being checked so the
    rejection says which boundary crossing was refused rather than only that one was.

    Raises `PolicyRejection` naming `credential-boundary` (TIS §0.2 — a gate refusing an
    operation aborts with the gate's identity).
    """
    leaks = _reachable_credentials(value, "", set())
    if leaks:
        raise PolicyRejection(
            CREDENTIAL_BOUNDARY,
            f"{what} would carry a credential across the context boundary at "
            f"{sorted(leaks)}. STD-19 confines secrets to Ingest; E5 §13 forbids "
            f"persisting one to an artifact or logging one.",
        )


__all__ = [
    "CREDENTIAL_BOUNDARY",
    "Credential",
    "REDACTED",
    "SECRET_FIELD_NAMES",
    "assert_credential_free",
]
