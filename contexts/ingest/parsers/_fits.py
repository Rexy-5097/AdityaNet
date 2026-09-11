"""Strict FITS access. Every lookup fails loud; none has a default.

`SPEC-parsers@r6` §5 opens with the rule this module exists to make unbreakable:

> **No default-on-missing-key** (`header.get(K, default)` is banned for any physically
> meaningful key — that idiom is the direct cause of v1's thirty-sprint failure).

The concrete failure was F-05: v1 defaulted `MJDREF` to 58484 where the archive declares
40587, producing a **~49-year** timestamp error that nothing detected. A default is not a
convenience — it is a fabricated measurement wearing the shape of a real one.

So there is no `get` here. `keyword()` raises. `column()` raises. A caller who wants a
tolerated absence must say so at the call site, in one place, with a reason — as `.hk`
absence is tolerated for v1.0 archives (§2.4) and an empty GTI is tolerated for SDD1 (F-12).

RELOCATED BY M3/E5/#18. It was written for the three SoLEXS parsers and lived beside them;
the six HEL1OS parsers need the same ban, and importing it out of a sibling instrument's
package would make one instrument's internals another's dependency. Nine call sites now,
across two instruments — STD-11's two-instance rule satisfied twice over.

The move changes no behaviour and no boundary: this module still imports only `domain.errors`,
it knows no instrument's conventions, SoLEXS's `lc`, `pi` and `gti` call it exactly as before,
and neither instrument package imports the other (asserted by the HEL1OS unit tests). #18 adds
one accessor, `declared_unit`, so that a declared unit is read with the same no-default
discipline as a keyword or a column.
"""

from __future__ import annotations

from typing import Any

from domain.errors import ContractViolation


def fail(rule: str, pointer: str, message: str) -> None:
    """Terminate with a diagnostic naming file, HDU and expectation (§5).

    `ContractViolation` is the TIS §0.2 class for *"input fails its schema or an invariant"*.
    The F-rule identifier is carried in the message rather than in a new exception type,
    because §0.2 permits exactly five failure classes and no others.
    """
    raise ContractViolation(pointer, f"{rule}: {message}")


def hdu(hdul: Any, name: str, *, source: str) -> Any:
    """Fetch an HDU **by name**. F-02: HDU order is not a contract.

    v1 read HDUs positionally. The archive's ordering happens to be stable, which is exactly
    what makes a positional read dangerous: it works until it does not, and then it reads a
    different HDU rather than failing.
    """
    try:
        return hdul[name]
    except KeyError:
        present = [x.name for x in hdul]
        fail("F-02", f"/{source}", f"HDU {name!r} absent; present by name: {present}")


def keyword(header: Any, key: str, *, source: str, hdu_name: str) -> Any:
    """Fetch a header keyword. Absent is F-04/F-05 territory, never a default."""
    if key not in header:
        fail(
            "F-05",
            f"/{source}#{hdu_name}/{key}",
            f"keyword {key!r} absent from HDU {hdu_name!r}. A default here is how v1 "
            f"produced a ~49-year timestamp error (§5).",
        )
    return header[key]


def expect(
    header: Any, key: str, expected: Any, *, source: str, hdu_name: str, rule: str
) -> Any:
    """Fetch a keyword and require an exact value."""
    actual = keyword(header, key, source=source, hdu_name=hdu_name)
    if actual != expected:
        fail(
            rule,
            f"/{source}#{hdu_name}/{key}",
            f"{key} is {actual!r}, expected {expected!r}",
        )
    return actual


def column(table: Any, name: str, *, source: str, hdu_name: str) -> Any:
    """Fetch a column by name, case-insensitively. F-04.

    Case-insensitive because FITS column names are not case-sensitive by the standard, and a
    case difference is a spelling of the same column rather than a different one. Absence is
    still fatal: *"v1 sought `RATE`; real is `COUNTS`"* is F-04's stated origin, and a parser
    that silently produced no column would have reproduced it.
    """
    wanted = name.upper()
    for candidate in table.columns.names:
        if candidate.upper() == wanted:
            return table.data[candidate]
    fail(
        "F-04",
        f"/{source}#{hdu_name}/{name}",
        f"column {name!r} absent; present: {list(table.columns.names)}",
    )


def declared_unit(table: Any, name: str, *, source: str, hdu_name: str) -> str | None:
    """The unit a column declares (`TUNITn`), or `None` when the product declares none.

    `None` is returned as data, not replaced: an undeclared unit is a fact about the product
    that a caller must handle at the call site, as §2.8 does for `czt2enth` (§8 A-4). The column
    itself must exist — absence is F-04, exactly as in `column`.
    """
    wanted = name.upper()
    for candidate in table.columns:
        if candidate.name.upper() == wanted:
            return None if candidate.unit is None else str(candidate.unit)
    fail(
        "F-04",
        f"/{source}#{hdu_name}/{name}",
        f"column {name!r} absent; present: {list(table.columns.names)}",
    )


__all__ = ["column", "declared_unit", "expect", "fail", "hdu", "keyword"]
