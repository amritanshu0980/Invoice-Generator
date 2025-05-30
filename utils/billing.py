import json

def load_product_data(json_path="product_data.json"):
    with open(json_path, "r") as f:
        return json.load(f)

def calculate_invoice(user_order, product_data):
    invoice_items = []
    subtotal = 0
    total_gst = 0
    total_installation = 0

    for product_name, qty in user_order.items():
        product = next((p for p in product_data if p["name"].lower() == product_name.lower()), None)
        if not product:
            continue

        price = product["price_excl_gst"]
        gst_rate = product.get("gst_rate", 18)
        install = product.get("installation_charge", 0)

        gst_amount = (price * gst_rate / 100) * qty
        line_total = (price * qty) + gst_amount + (install * qty)

        subtotal += price * qty
        total_gst += gst_amount
        total_installation += install * qty

        invoice_items.append({
            "name": product["name"],
            "qty": qty,
            "unit_price": price,
            "gst_rate": gst_rate,
            "gst_amount": round(gst_amount, 2),
            "installation_charge": install,
            "total": round(line_total, 2)
        })

    return {
        "items": invoice_items,
        "summary": {
            "subtotal": round(subtotal, 2),
            "total_gst": round(total_gst, 2),
            "total_installation": round(total_installation, 2),
            "grand_total": round(subtotal + total_gst + total_installation, 2)
        }
    }
