import sys
import torch
import numpy
import pandas
import platform
import json

info = {
    "python_version": sys.version,
    "torch_version": torch.__version__,
    "numpy_version": numpy.__version__,
    "pandas_version": pandas.__version__,
    "system_platform": platform.platform(),
    "system_processor": platform.processor(),
    "mps_available": torch.backends.mps.is_available(),
    "cuda_available": torch.cuda.is_available(),
}

print(json.dumps(info, indent=2))
