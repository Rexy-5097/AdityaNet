import json

with open("scratch/verification_checklist_results.json", "r") as f:
    data = json.load(f)

for section, verifs in data.items():
    print("="*60)
    print(f"SECTION: {section}")
    for v in verifs:
        print(f"  CLAIM: {v['claim']}")
        print(f"  RESULT: {v['result']}")
        print(f"  FILE: {v['file']}")
        print(f"  LINE: {v['line']}")
        # print first few items of value or truncated string representation
        val_str = str(v['value'])
        if len(val_str) > 500:
            val_str = val_str[:500] + "... [TRUNCATED]"
        print(f"  VALUE: {val_str}")
        print("-" * 40)
