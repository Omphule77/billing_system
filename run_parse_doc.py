import re

with open('debug_wa.html', 'r', encoding='utf-8') as f:
    content = f.read()

print("--- Occurrences of 'Document' ---")
# Find 'Document' with context
matches = re.finditer(r'(.{50}Document.{50})', content)
for m in matches:
    print(f"...{m.group(1)}...")
