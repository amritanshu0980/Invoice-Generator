import os
import json
from PyMuPDF import fitz
import docx
import re
import csv
import google.generativeai as genai

# 1. Set up Gemini API
genai.configure(api_key="AIzaSyANAvtypU-WcvNwoCKGeBg_z1_68uq1-hU")  # Replace with your actual API key
model = genai.GenerativeModel("gemini-2.0-flash")

# 2. Read different document formats
def extract_text(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext == ".docx":
        return extract_from_docx(file_path)
    elif ext == ".xlsx":
        return extract_from_excel(file_path)
    elif ext == ".csv":
        return extract_from_csv(file_path)
    else:
        raise ValueError("Unsupported file type")

def extract_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join(page.get_text() for page in doc)

def extract_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_from_excel(file_path):
    import openpyxl
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    text = ""
    for row in sheet.iter_rows(values_only=True):
        text += " | ".join(str(cell) for cell in row if cell is not None) + "\n"
    return text

def extract_from_csv(file_path):
    text = ""
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            text += " | ".join(row) + "\n"
    return text

# 3. Prompt Gemini to extract structured product info
def extract_product_data(text):
    prompt = f"""
Extract product details from the text below.
Return ONLY a valid JSON array like this:

[
  {{
    "name": "Product Name",
    "price_excl_gst": 123.45,
    "gst_rate": 18,
    "installation_charge": 50
  }},
  ...
]

Document:
{text}
"""
    response = model.generate_content(prompt)
    raw = response.text.strip()
    print("🔍 Gemini raw response:\n", raw)

    # Remove ```json and ``` if present
    raw = re.sub(r"```json|```", "", raw, flags=re.IGNORECASE).strip()

    # Extract the JSON array using regex
    match = re.search(r"\[\s*{.*?}\s*\]", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            print("❌ JSON decode error.")
            print(match.group(0))
            return []
    else:
        print("❌ No JSON found in response.")
        return []

# 4. Main method to run the pipeline
def process_document(file_path):
    text = extract_text(file_path)
    product_data = extract_product_data(text)
    with open("product_data.json", "w") as f:
        json.dump(product_data, f, indent=2)
    print("✅ Extracted data saved to: product_data.json")
    return product_data

# Example usage
if __name__ == "__main__":
    test_file = "products.csv"  # Replace with your desired test file
    process_document(test_file)
