import re

filename = 'debug_wa_send.html'
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"--- Parsing {filename} ---")

# Find button with aria-label="Send" and print full tag
matches = re.finditer(r'(<button[^>]*aria-label="Send"[^>]*>)', content)
for m in matches:
    print(f"Button Tag: {m.group(1)}")

# Find span with data-icon="send" or wds-ic-send-filled
matches = re.finditer(r'(<span[^>]*data-icon="(?:send|wds-ic-send-filled)"[^>]*>)', content)
for m in matches:
    print(f"Span Tag: {m.group(1)}")
    
# Check for overlays
if "overlay" in content:
    print("WARNING: 'overlay' found in HTML")
