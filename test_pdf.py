from app.utils import generate_pdf
import os

html = "<html><body><h1>Test Bill</h1><p>Amount: $100</p></body></html>"
path = "test_bill.pdf"

success = generate_pdf(html, path)
print(f"Generation Success: {success}")

if success:
    size = os.path.getsize(path)
    print(f"File Size: {size}")
    if size > 100:
        print("PDF appears valid (size > 100 bytes).")
    else:
        print("PDF is too small/empty.")
else:
    print("Generation Failed.")
