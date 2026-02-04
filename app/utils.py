from xhtml2pdf import pisa
from io import BytesIO
import os

def generate_pdf(html_content, output_path):
    """
    Generates a PDF from HTML content and saves it to output_path.
    """
    try:
        # Ensure directory exists
        if os.path.dirname(output_path):
             os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(
                html_content,                # the HTML to convert
                dest=pdf_file                # file handle to recieve result
            )
            
        return not pisa_status.err
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return False
