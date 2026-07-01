import os
import time

dir_path = "artifacts/sprint18a"
for f in os.listdir(dir_path):
    p = os.path.join(dir_path, f)
    mtime = os.path.getmtime(p)
    print(f"{f}: size={os.path.getsize(p)}, mtime={time.ctime(mtime)}")
