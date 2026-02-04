import re

with open('debug_wa.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("--- Titles ---")
titles = re.findall(r'title="([^"]+)"', content)
for t in titles:
    if "ttach" in t or "lus" in t:
        print(f"Found title: {t}")

print("\n--- Aria Labels ---")
arias = re.findall(r'aria-label="([^"]+)"', content)
for a in arias:
    if "ttach" in a or "lus" in a:
        print(f"Found aria-label: {a}")

print("\n--- Data Icons ---")
icons = re.findall(r'data-icon="([^"]+)"', content)
for i in icons:
    if "lus" in i or "clip" in i:
        print(f"Found data-icon: {i}")

print("\n--- All Data Icons (first 20) ---")
for i in icons[:20]:
    print(i)
