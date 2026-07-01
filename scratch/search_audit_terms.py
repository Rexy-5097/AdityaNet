import os

search_dir = "/Users/soumyadebtripathy/AdityaNet"
search_terms = ["fact", "fact_id", "project state audit", "fact registry"]

for root, dirs, files in os.walk(search_dir):
    if "venv" in root or ".git" in root:
        continue
    for file in files:
        if file.endswith((".md", ".json", ".py", ".sh", ".txt")):
            path = os.path.join(root, file)
            try:
                with open(path, "r", errors="ignore") as f:
                    content = f.read().lower()
                for term in search_terms:
                    if term in content:
                        print(f"Found '{term}' in {os.path.relpath(path, search_dir)}")
            except Exception as e:
                pass
