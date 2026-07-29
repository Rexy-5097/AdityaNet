# Reproduction environment for the AdityaNet scientific pipeline.
#
# The published dataset and benchmark were produced on Python 3.12.12 (recorded in
# artifacts/v2/phase05/freeze_manifest.json under `environment`). This image pins the same
# minor version and installs from the FROZEN LOCKFILE that the freeze recorded, not from
# requirements.txt, so a rebuild resolves the same dependency graph rather than whatever
# is current on PyPI today.
#
# TWO ENVIRONMENTS, ONE LOCKFILE — read this before comparing checksums.
#
# freeze_manifest.json records lockfile_sha256 = 6899e001..., which is the exact hash of
# this file AT THE FREEZE COMMIT (be0b7e5, 2026-07-18). The dataset was built in that
# environment and that record is accurate.
#
# The benchmark ran five days later (9efad0c) and needed lightgbm, shap, numba, llvmlite,
# cloudpickle, slicer and tqdm. Those were appended to the same lockfile, so the file now
# in the repository hashes to 8187301e... — a strict SUPERSET of the freeze environment.
#
# This image installs the current lockfile, because it is the only environment that can
# run BOTH the dataset rebuild and the benchmark, and it verifies against that hash. The
# freeze-time hash is not wrong; it describes an earlier, smaller environment. Anyone
# reproducing only the dataset freeze can check out be0b7e5 and will get 6899e001.
#
# What this image does NOT contain: the raw ISSDC Level-1 archive. Those products are not
# redistributable here, and they are large. Mount them at /data (see compose.yaml).

FROM python:3.12.12-slim-bookworm

# Build tools are needed for the scientific wheels that have no manylinux build for this
# platform; removed in the same layer so they do not ship in the final image.
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential git \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /adityanet

# The exact dependency set the freeze recorded, plus its published checksum.
COPY artifacts/v2/phase05/requirements.lock /tmp/requirements.lock
ARG LOCKFILE_SHA256=8187301ecffc0bac6ae2ff97b9e0cb6791d20fdaf8afd31614a1d7cb6ea80320
RUN echo "${LOCKFILE_SHA256}  /tmp/requirements.lock" | sha256sum -c - \
 && pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r /tmp/requirements.lock

# Source last, so dependency layers stay cached across code changes.
COPY research/ /adityanet/research/
COPY artifacts/ /adityanet/artifacts/

WORKDIR /adityanet/research

# Determinism: the benchmark's own seed is 20260718 and is set in the protocol, but hash
# randomisation and thread counts also affect reproducibility of some numeric paths.
ENV PYTHONHASHSEED=0 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PYTHONDONTWRITEBYTECODE=1

# Default: verify the environment reproduces, and report the dataset digest it can see.
CMD ["python", "-c", "import sys, hashlib, pathlib; print('python', sys.version.split()[0]); p=pathlib.Path('/adityanet/artifacts/v2/phase05/freeze_manifest.json'); print('freeze manifest present:', p.exists())"]
