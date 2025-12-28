
with open('tmp/profile_full.json', 'r') as f:
    for i, line in enumerate(f):
        if 'inventory' in line:
            print(f"Found inventory at line {i+1}: {line.strip()[:100]}...")
            break
