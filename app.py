try:
    import streamlit as st
    import cv2
    import numpy as np
    from pyzbar.pyzbar import decode
    import json
    import os
    import barcode
except ModuleNotFoundError as e:
    raise ImportError("Required module not found. Ensure 'streamlit', 'opencv-python', 'numpy', and 'pyzbar' are installed.") from e

# Ensure 'items' folder exists
if not os.path.exists("items"):
    os.makedirs("items")

# Streamlit Page Configuration
st.set_page_config(page_title="Scan Barcode", page_icon="📸", layout="wide")

st.title("📸 Scan Your Products")
st.write("Scan a barcode and retrieve product details instantly.")

# Layout: Two columns
col1, col2 = st.columns([1, 1])

# Initialize webcam capture
cap = cv2.VideoCapture(0)
barcode_data = None

FRAME_WINDOW = col1.image([])
scan_active = col1.button("📷 Capture & Detect")

def scan_barcode():
    global barcode_data
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        for barcode in decode(frame):
            barcode_data = barcode.data.decode('utf-8')
            rect = barcode.rect
            cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 255, 0), 2)
            cap.release()
            cv2.destroyAllWindows()
            return barcode_data
        FRAME_WINDOW.image(frame, channels="BGR")
    return None

if scan_active or not barcode_data:
    barcode_data = scan_barcode()
    
if barcode_data:
    col2.success(f"**Barcode Detected:** `{barcode_data}`")
    
    # Fetch product details
    product = barcode.get_product_details(barcode_data)
    
    if product:
        col2.image(product.get("image_url", "https://via.placeholder.com/150"), width=250)
        
        allergens = []
        attribute_groups = product.get('attribute_groups', [])
        for group in attribute_groups:
            if group.get('id') == 'allergens':
                for attribute in group.get('attributes', []):
                    title = attribute.get('title', '')
                    if "Contient" in title:
                        allergens.append(f"<span style='color:red;'>{title.replace('Contient : ', '')}</span>")
                    elif "Peut contenir" in title:
                        allergens.append(f"<span style='color:orange;'>{title.replace('Peut contenir : ', '')}</span>")
        
        # Display allergen tags if any exist
        if allergens:
            col2.markdown("**Allergens:** " + " | ".join(allergens), unsafe_allow_html=True)
            
        with st.expander("Nutritional Information"):
            nutriments = product.get("nutriments", {})
            for key, value in nutriments.items():
                if isinstance(value, (int, float)):
                    st.write(f"- {key.replace('_100g', '').replace('_', ' ').capitalize()}: {value}")
        
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

cap.release()
cv2.destroyAllWindows()
