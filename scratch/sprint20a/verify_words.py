import os
import re

FORBIDDEN_WORDS = [
    "recommend", "should", "better", "best", "good", "bad", 
    "improve", "issue", "problem", "technical debt", "restart", 
    "continue", "replace", "keep", "remove", "fix", "optimize", 
    "severity", "critical", "major", "minor", "important", 
    "priority", "risk", "ready", "complete", "incomplete", 
    "success", "failure", "correct", "incorrect"
]

out_dir = "artifacts/sprint20a"
files = os.listdir(out_dir)

print(f"Scanning {len(files)} files for forbidden words...")
total_found = 0

for file in files:
    file_path = os.path.join(out_dir, file)
    if os.path.isdir(file_path):
        continue
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    found_words = []
    for word in FORBIDDEN_WORDS:
        pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
        if pattern.search(content):
            found_words.append(word)
            
    if found_words:
        print(f"Forbidden word(s) found in {file}: {found_words}")
        total_found += len(found_words)

if total_found == 0:
    print("Zero forbidden words found! Scan clean.")
else:
    print(f"Total violations found: {total_found}")
