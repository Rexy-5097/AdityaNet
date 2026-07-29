"""Failure classes raised by the provenance kernel.

TIS §0.2 defines a five-class taxonomy for the whole system. The kernel raises exactly two
of them, so exactly two are defined here. Declaring the other three would be speculative:
they belong to the contexts that raise them, and an unused exception class is a contract
nobody has tested.

STD-13: errors fail loud. There is no fallback, no default-on-error and no bare except
anywhere in this package. A digest that cannot be computed is never substituted.
"""

from __future__ import annotations


class KernelError(Exception):
    """Base for every failure this package raises."""


class IntegrityFailure(KernelError):
    """Bytes are not what they were claimed to be.

    Raised on a digest mismatch, a truncated read, or a stored record whose content does not
    hash to the name it is stored under. Never recoverable in place: the caller must abort
    rather than retry against the same bytes.
    """


class ProvenanceFailure(KernelError):
    """The provenance graph would become unsound.

    Raised when a record references an input that was never registered, when a record would
    close a cycle, or when a Run is transitioned out of order. These are all conditions
    under which the DAG would stop answering "where did this come from" correctly.
    """
