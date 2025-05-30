# utils/extract_with_gemini.py

import os
import json
import fitz  # PyMuPDF
import docx
import openpyxl
import google.generativeai as genai

# 1. Set up Gemini API
genai.configure(api_key="xyz")

model = genai.GenerativeModel("gemini-2.0-flash")

# 2. Read different document formats
def extract_text(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return extract_from_pdf(file_path)
    elif ext in [".docx"]:
        return extract_from_docx(file_path)
    elif ext in [".xlsx"]:
        return extract_from_excel(file_path)
    else:
        raise ValueError("Unsupported file type")

def extract_from_pdf(file_path):
    doc = fitz.open(file_path)
    return "\n".join(page.get_text() for page in doc)

def extract_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join(p.text for p in doc.paragraphs)

def extract_from_excel(file_path):
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    text = ""
    for row in sheet.iter_rows(values_only=True):
        text += " | ".join(str(cell) for cell in row if cell is not None) + "\n"
    return text

# 3. Prompt Gemini to extract structured product info
def extract_product_data(text):
    prompt = f"""
You are a helpful assistant. Extract product details from the text below.
Return the output in this exact JSON format:

[
  {{
    "name": "Product Name",
    "price_excl_gst": number,
    "gst_rate": number,
    "installation_charge": number
  }},
  ...
]

Here is the document content:
{text}
"""
    response = model.generate_content(prompt)
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        print("❌ Error decoding JSON from Gemini output.")
        print(response.text)
        return []

# 4. Main method to run the pipeline
def process_document(file_path):
    text = extract_text(file_path)
    product_data = extract_product_data(text)
    with open("product_data.json", "w") as f:
        json.dump(product_data, f, indent=2)
    print(f"✅ Extracted data saved to: product_data.json")
    return product_data

# Example usage
if __name__ == "__main__":
    test_file = "products.csv"  # Change to your file path
    process_document(test_file)
