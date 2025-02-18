import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import json
import os
import pandas as pd

# Ensure 'items' folder exists
if not os.path.exists("items"):
    os.makedirs("items")

# Streamlit Page Configuration
st.set_page_config(page_title="Scan Barcode", page_icon="📸", layout="wide")

st.title("📸 Scan Your Products")
st.write("Upload a barcode image to retrieve product details instantly.")

# Layout: Two columns
col1, col2 = st.columns([1, 1])

# File uploader for barcode image
uploaded_file = col1.file_uploader("Upload an image with a barcode", type=["jpg", "png", "jpeg"])

barcode_data = None

def scan_barcode(image):
    """Scan barcode from uploaded image."""
    global barcode_data
    image_array = np.array(bytearray(image.read()), dtype=np.uint8)
    frame = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

    for barcode in decode(frame):
        barcode_data = barcode.data.decode('utf-8')
        rect = barcode.rect
        cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 255, 0), 2)
        return barcode_data
    return None

if uploaded_file:
    barcode_data = scan_barcode(uploaded_file)

if barcode_data:
    col2.success(f"**Barcode Detected:** `{barcode_data}`")
    
    # Fetch product details from OpenFoodFacts API
    import requests
    response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode_data}.json")
    product_data = response.json()

    if "product" in product_data:
        product = product_data["product"]

        col2.image(product.get("image_url", "https://via.placeholder.com/150"), width=250)

        # Extract and display allergens
        allergens = product.get("allergens", "No allergens listed.")
        col2.markdown(f"**Allergens:** {allergens}")

        # Display Ingredients Section
        ingredients_text = product.get("ingredients_text", "Ingredients not available.")

        with st.expander("📝 Ingredients"):
            formatted_ingredients = "- " + "\n- ".join(ingredients_text.split(", "))
            st.markdown(formatted_ingredients)

        # Improved Nutritional Information Display
        with st.expander("Nutritional Information"):
            nutriments = product.get("nutriments", {})
            df_nutrients = pd.DataFrame(list(nutriments.items()), columns=["Nutrient", "Value"])
            df_nutrients = df_nutrients[df_nutrients["Nutrient"].str.contains("_100g")]
            df_nutrients["Nutrient"] = df_nutrients["Nutrient"].str.replace("_100g", "").str.replace("_", " ").str.capitalize()
            df_nutrients["Value"] = df_nutrients["Value"].astype(float).round(1)
            st.table(df_nutrients)

        with st.expander("Additional Information"):
            st.write(f"**[OpenFoodFacts URL]({product.get('url', 'N/A')})**")

        # Save JSON Button
        json_data = json.dumps(product, indent=4)
        file_path = os.path.join("items", f"product_{barcode_data}.json")
        with open(file_path, "w") as json_file:
            json_file.write(json_data)

        st.download_button(
            label="💾 Save as JSON",
            file_name=f"product_{barcode_data}.json",
            mime="application/json",
            data=json_data
        )
    else:
        col2.error("Product not found.")
