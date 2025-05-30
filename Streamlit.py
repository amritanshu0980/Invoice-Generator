
import os
import json
import streamlit as st
from datetime import datetime
from extract_with_gemini_setup_level import process_document
from utils.billing import calculate_invoice
from jinja2 import Environment, FileSystemLoader
import pdfkit
from num2words import num2words
import re

# Paths
TEMPLATE_PATH = "templates"
PRODUCT_DATA_PATH = "product_data.json"

st.set_page_config(page_title="Invoice Chat Assistant")
st.title("🧾 Invoice Chat Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "cart" not in st.session_state:
    st.session_state.cart = {}
if "client" not in st.session_state:
    st.session_state.client = {}
if "invoice_ready" not in st.session_state:
    st.session_state.invoice_ready = False

# Sidebar: Upload
st.sidebar.subheader("📂 Upload Product Document")
uploaded_file = st.sidebar.file_uploader("Upload a PDF, DOCX or XLSX file", type=["pdf", "docx", "xlsx"])

if uploaded_file:
    file_path = os.path.join("uploads", uploaded_file.name)
    os.makedirs("uploads", exist_ok=True)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.sidebar.success("Parsing document...")
    process_document(file_path)
    st.sidebar.success("✅ Products updated!")

# Sidebar: Client Info
with st.sidebar.form("client_form"):
    st.markdown("👤 Enter Client Details")
    name = st.text_input("Client Name")
    address = st.text_input("Address")
    gst_number = st.text_input("GST Number")
    supply = st.text_input("Place of Supply")
    submit = st.form_submit_button("Save Client Info")
    if submit:
        st.session_state.client = {
            "name": name, "address": address,
            "gst_number": gst_number, "place_of_supply": supply
        }
        st.sidebar.success("✅ Client info saved.")

def load_products():
    try:
        with open(PRODUCT_DATA_PATH, "r") as f:
            return json.load(f)
    except:
        return []

products = load_products()
product_names = [p["name"] for p in products]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_input = st.chat_input("Type a message or command...")

if user_input:
    st.chat_message("user").markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    response = ""

    if "add" in user_input.lower():
        for name in product_names:
            if name.lower() in user_input.lower():
                qty_match = re.search(r"(\d+)", user_input)
                qty = int(qty_match.group(1)) if qty_match else 1
                st.session_state.cart[name] = st.session_state.cart.get(name, 0) + qty
                response = f"✅ Added {qty} x {name} to the cart."
                break
        else:
            response = "❌ Couldn't find a matching product. Try again."

    elif "remove" in user_input.lower() or "delete" in user_input.lower():
        found = False
        for name in list(st.session_state.cart.keys()):
            if name.lower() in user_input.lower():
                qty_match = re.search(r"(\d+)", user_input)
                qty = int(qty_match.group(1)) if qty_match else None

                if qty:
                    if st.session_state.cart[name] > qty:
                        st.session_state.cart[name] -= qty
                        response = f"🔻 Removed {qty} x {name} from cart."
                    else:
                        st.session_state.cart.pop(name)
                        response = f"❌ Removed all of '{name}' from cart."
                else:
                    st.session_state.cart.pop(name)
                    response = f"❌ Removed '{name}' from cart."
                found = True
                break
        if not found:
            response = "⚠️ Couldn't match any product in your cart to remove."

    elif "cart" in user_input.lower():
        if not st.session_state.cart:
            response = "🛒 Your cart is empty."
        else:
            lines = ["🧾 Items in your cart:"]
            for name, qty in st.session_state.cart.items():
                lines.append(f"- {name}: {qty}")
            response = "\n".join(lines)

    elif "client" in user_input.lower():
        response = "👤 Please enter client details using the sidebar form."

    elif "generate invoice" in user_input.lower():
        if not st.session_state.cart or not st.session_state.client:
            response = "❌ Please add products and client info first."
        else:
            invoice = calculate_invoice(st.session_state.cart, products)
            context = {
                "client": st.session_state.client,
                "seller": {
                    "name": "Rohan Pvt Ltd",
                    "address": "Xyz, Cunningham Road, Bangalore",
                    "gstin": "29AANPC1234A1Z1"
                },
                "invoice_number": "1",
                "invoice_date": datetime.today().strftime("%d-%b-%Y"),
                "supplier_ref": "20",
                "other_ref": "",
                "invoice": invoice,
                "amount_in_words": num2words(invoice["summary"]["grand_total"], to="currency", lang="en_IN").title(),
                "tax_in_words": num2words(invoice["summary"]["total_gst"], to="currency", lang="en_IN").title()
            }

            env = Environment(loader=FileSystemLoader(TEMPLATE_PATH))
            template = env.get_template("invoice_template.html")
            html = template.render(**context)

            with open("invoice_preview.html", "w", encoding="utf-8") as f:
                f.write(html)

            pdfkit.from_file("invoice_preview.html", "invoice_output.pdf")
            st.session_state.invoice_ready = True
            response = "📄 Invoice created and ready to download."

    else:
        response = "💡 Try: 'add 2 CCTV setups', 'remove 5 CCTV setups', 'show cart', 'client info', or 'generate invoice'"

    st.chat_message("assistant").markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

# Show download button if invoice is ready
if st.session_state.invoice_ready:
    with open("invoice_output.pdf", "rb") as pdf_file:
        st.download_button("📥 Download Invoice", data=pdf_file, file_name="invoice_output.pdf")
