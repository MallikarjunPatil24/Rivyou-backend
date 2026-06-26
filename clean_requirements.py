import os

req_path = 'requirements.txt'
if os.path.exists(req_path):
    try:
        # Read as UTF-16 LE
        with open(req_path, 'r', encoding='utf-16') as f:
            content = f.read()
        
        # Write back as UTF-8
        with open(req_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully converted requirements.txt to UTF-8")
    except Exception as e:
        print(f"Could not convert encoding: {e}")
