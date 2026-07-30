# Salvaged design knowledge

Design intent extracted from the v1 generation before its removal by M1/E2/#9.

**These documents are not specifications.** They mandate nothing and govern no code. A
specification in `specs/parsers/` is a contract the implementation must satisfy; a salvage
document is a record of what a previous generation learned, kept so the learning is not
repeated at full cost. Binding decisions live in [`adr/`](../../adr/index.md).

## Why salvage at all

Issue #9 deletes roughly 22,900 lines. The code deserves deletion — v1's Aditya-L1 data was
synthetic and its Aditya conclusions are void. But three parts of it encode judgement that
was expensive to acquire and is not visible from the outside: an acquisition path whose
output was independently verified against the real solar record, a feature framework whose
discipline was sound, and an integrity system built in response to a proven data leak.

Deleting the code without recording that judgement would mean rediscovering it. Keeping the
code to preserve it would mean carrying 22,900 lines in every clone. These documents are the
third option.

| ID | Subject | Source at `v1-surya-final` | LOC |
| --- | --- | --- | --- |
| [SALVAGE-001](SALVAGE-001.md) | GOES ingestion and backfill | `services/ingestion/`, `services/backfill/` | 1,408 |
| [SALVAGE-002](SALVAGE-002.md) | The v4 feature framework, and the gate it lacked | `services/ml/features_v4/framework.py` | 95 |
| [SALVAGE-003](SALVAGE-003.md) | Versioned operator policy, integrity under a proven leak | `services/ml/policy.py` | 446 |

## Reading them honestly

Each document has three parts: what v1 got right, what the frozen architecture does
differently, and what must not be carried forward. The third section matters most. Salvage
is a standing invitation to reintroduce something that was removed for a reason, so every
document states explicitly which parts are ideas and which are artifacts fitted on data that
is now known to be unusable.

[SALVAGE-002](SALVAGE-002.md) is the one to read first. The v1 feature framework recorded,
per feature, exactly the instrument metadata that would have prevented the project's central
failure — and nothing ever compared it against anything. That is the origin of
[ADR-0011](../../adr/ADR-0011.md), and the reason its regression test is a required CI check.

## Recovering the implementation

```
git show v1-surya-final:<path>                          # inspect one file
git checkout v1-surya-final -- <path>                   # restore into the working tree
git worktree add --detach /tmp/v1-surya v1-surya-final  # browse the whole generation
```
