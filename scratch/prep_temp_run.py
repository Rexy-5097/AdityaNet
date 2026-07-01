import shutil

# Copy original script to a temporary runner
shutil.copy("scratch/sprint18a/root_cause_analysis.py", "scratch/temp_run.py")

# Modify it to run only 1 bootstrap iteration
with open("scratch/temp_run.py", "r") as f:
    code = f.read()

# Replace bootstrap count
code = code.replace("n_iterations=10000", "n_iterations=1")

with open("scratch/temp_run.py", "w") as f:
    f.write(code)

print("Modification complete. Ready to run scratch/temp_run.py.")
