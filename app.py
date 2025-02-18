import streamlit as st
import numpy as np
import cv2
from PIL import Image
import json
import os
import pandas as pd
import requests
import pyzxing  # ZXing barcode reader

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

def preprocess_image(image):
    """Enhance image for barcode detection"""
    image = Image.open(image).convert("L")  # Convert to grayscale
    image = np.array(image)

    # Apply adaptive threshold for better contrast
    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)

    # Rotate image if barcode is vertical
    if image.shape[0] > image.shape[1]:  # If height > width, rotate
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)

    return image

def scan_barcode(image):
    """Extract barcode using ZXing"""
    reader = pyzxing.BarCodeReader()
    
    # Save uploaded image temporarily
    image_path = "temp_barcode.jpg"
    processed_image = preprocess_image(image)
    cv2.imwrite(image_path, processed_image)

    # Decode barcode
    barcode = reader.decode(image_path)
    
    if barcode and barcode[0]['parsed']:
        return barcode[0]['parsed']
    
    return None

if uploaded_file:
    # Show the uploaded image
    col1.image(uploaded_file, caption="Uploaded Image", use_container_width=True)

    # Scan barcode from the image
    barcode_data = scan_barcode(uploaded_file)

    if barcode_data:
        col2.success(f"**Barcode Detected:** `{barcode_data}`")

        # Fetch product details from OpenFoodFacts API
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

            # Save JS
