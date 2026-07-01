import os

def main():
    paths = ["data", "data/aditya_l1", "data/aditya_l1/processed", "data/aditya_l1/raw"]
    for p in paths:
        print(f"Path '{p}' exists: {os.path.exists(p)}")
        if os.path.exists(p) and os.path.isdir(p):
            print(f"  Contents: {os.listdir(p)[:10]}")

if __name__ == "__main__":
    main()
