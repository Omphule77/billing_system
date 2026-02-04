import re

filename = 'debug_wa_send.html'
with open(filename, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"--- Parsing {filename} ---")

# Find wds-ic-send-filled and surrounding tag
matches = re.finditer(r'<(\w+)[^>]*data-icon="wds-ic-send-filled"[^>]*>', content)
found = False
for m in matches:
    found = True
    print(f"Found match: {m.group(0)}")

if not found:
    print("wds-ic-send-filled NOT FOUND")

# Check for aria-label="Send"
matches = re.finditer(r'<(\w+)[^>]*aria-label="Send"[^>]*>', content)
for m in matches:
    print(f"Found aria-label match: {m.group(0)}")

# Check for just 'send' icon
matches = re.finditer(r'<(\w+)[^>]*data-icon="send"[^>]*>', content)
for m in matches:
    print(f"Found data-icon='send' match: {m.group(0)}")
