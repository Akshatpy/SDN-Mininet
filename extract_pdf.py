import pdfplumber

pdf1_path = "SDN Mininet - Orange_Student_Guidelines.pdf"
pdf2_path = "Mininet Installation Guide on UBUNTU.docx.pdf"

print("=" * 80)
print("PDF 1: SDN Mininet - Orange_Student_Guidelines.pdf")
print("=" * 80)
try:
    with pdfplumber.open(pdf1_path) as pdf:
        for i, page in enumerate(pdf.pages):
            print(f"\n--- PAGE {i+1} ---")
            text = page.extract_text()
            if text:
                print(text[:2000])  # Print first 2000 chars of each page
except Exception as e:
    print(f"Error reading PDF 1: {e}")

print("\n" + "=" * 80)
print("PDF 2: Mininet Installation Guide on UBUNTU.docx.pdf")
print("=" * 80)
try:
    with pdfplumber.open(pdf2_path) as pdf:
        for i, page in enumerate(pdf.pages[:3]):  # First 3 pages
            print(f"\n--- PAGE {i+1} ---")
            text = page.extract_text()
            if text:
                print(text[:2000])
except Exception as e:
    print(f"Error reading PDF 2: {e}")
