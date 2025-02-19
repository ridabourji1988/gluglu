import streamlit as st
import os
import cv2
import numpy as np
from pyzbar.pyzbar import decode
import json
import pandas as pd
import barcode  # Custom barcode.py to fetch product details
import re

# ✅ Set Page Config
st.set_page_config(page_title="Scan Barcode", page_icon="📸", layout="wide")

# 🚀 Instructions for Remote Access
with st.expander("🚀 Comment accéder à l'application à distance (Cliquer pour développer)"):
    st.markdown("""
    1️⃣ **Ouvrir un nouveau terminal**  
    2️⃣ **Exécuter:**  
       ```bash
       ngrok authtoken YOUR_NGROK_AUTH_TOKEN
       ```
    3️⃣ **Exécuter:**  
       ```bash
       ngrok http 8503
       ```
    4️⃣ **Copiez l'URL générée par ngrok et collez-la dans votre navigateur.**  
    """)

if not os.path.exists("items"):
    os.makedirs("items")

st.title("📸 Scanner vos produits")
st.write("Scannez un code-barres et obtenez instantanément les détails du produit.")

# 🔍 Detect if running on Mobile or PC using JavaScript
st.markdown(
    """
    <script>
        function getDeviceType() {
            if (/Mobi|Android/i.test(navigator.userAgent)) {
                return "mobile";
            } else {
                return "desktop";
            }
        }
        document.getElementById("device-type").innerText = getDeviceType();
    </script>
    <div id="device-type"></div>
    """,
    unsafe_allow_html=True,
)

# Default device type
device_type = st.session_state.get("device_type", "unknown")

# ✅ Set Camera based on Device Type
if device_type == "mobile":
    st.info("📱 Mobile détecté : Activation de la caméra mobile.")
    cap = cv2.VideoCapture(1)  # Mobile Front Camera (adjust if needed)
else:
    st.info("💻 PC détecté : Activation de la webcam.")
    cap = cv2.VideoCapture(0)  # Default PC Webcam

col1, col2 = st.columns([1, 1])
FRAME_WINDOW = col1.image([])
scan_active = col1.button("📷 Capturer & Détecter")

# 🔹 Barcode Scanner Function
def scan_barcode():
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        for bc in decode(frame):
            barcode_data = bc.data.decode('utf-8')
            rect = bc.rect
            cv2.rectangle(frame, (rect.left, rect.top),
                          (rect.left + rect.width, rect.top + rect.height),
                          (0, 255, 0), 2)
            cap.release()
            cv2.destroyAllWindows()
            return barcode_data
        FRAME_WINDOW.image(frame, channels="BGR")
    return None

# ✅ Start scanning when button is pressed
if scan_active:
    barcode_data = scan_barcode()

if barcode_data:
    col2.success(f"**✅ Code-barres détecté:** `{barcode_data}`")

    # ─────────────────────────────────────────────
    # Fetch product details
    product = barcode.get_product_details(barcode_data)

    if product:
        col2.image(product.get("image_url", "https://via.placeholder.com/150"), width=250)
        st.write("🔍 **Produit trouvé:**", product.get("product_name", "Nom inconnu"))

        # ✅ Allergen Extraction
        allergens = []
        fallback_allergens_found = set()

        # 1️⃣ Extract allergens from attribute_groups
        attribute_groups = product.get('attribute_groups', [])
        for group in attribute_groups:
            for attr in group.get('attributes', []):
                title_attr = attr.get('title', '')
                if "Contient" in title_attr:
                    formatted = f"<span style='color:red;'>❗ {title_attr.replace('Contient : ', '')}</span>"
                    allergens.append(formatted)
                elif "Peut contenir" in title_attr:
                    formatted = f"<span style='color:orange;'>⚠️ {title_attr.replace('Peut contenir : ', '')}</span>"
                    allergens.append(formatted)

        # 2️⃣ Extract allergens from Ingredients
        ingredients_text = product.get("ingredients_text", "Ingrédients non disponibles.")
        known_allergens = ["blé", "beurre", "lait", "soja", "œufs", "graines de sésame", "fruits à coque", "amidon", "maïs", "noisettes", "cajou"]

        for known in known_allergens:
            pattern = re.compile(r'\b' + re.escape(known) + r'\b', re.IGNORECASE)
            if pattern.search(ingredients_text):
                fallback_allergens_found.add(known.capitalize())
            ingredients_text = pattern.sub(f"<strong style='color:red'>{known.capitalize()}</strong>", ingredients_text)

        # 3️⃣ Extract allergens from allergens_tags
        allergens_tags = product.get("allergens_tags", [])
        for tag in allergens_tags:
            tag_clean = tag.replace("fr:", "").replace("en:", "").capitalize()
            candidate = f"<span style='color:red;'>❗ {tag_clean}</span>"
            allergens.append(candidate)

        # Merge unique allergens
        for fallback_allergen in fallback_allergens_found:
            formatted = f"<span style='color:red;'>❗ {fallback_allergen}</span>"
            if formatted not in allergens:
                allergens.append(formatted)

        # Remove duplicates
        unique_allergens = list(dict.fromkeys(allergens))

        # ✅ Display Allergens
        if unique_allergens:
            formatted_allergens = " | ".join(unique_allergens)
            col2.markdown(f"🚨 **Allergènes:** {formatted_allergens}", unsafe_allow_html=True)
        else:
            col2.info("✅ Aucun allergène détecté.")

        # ✅ Display Ingredients with Highlights
        with st.expander("📝 Ingrédients (Cliquer pour développer)"):
            st.markdown(ingredients_text, unsafe_allow_html=True)

        # ✅ Display Nutritional Information
        with st.expander("📊 Informations nutritionnelles"):
            nutriments = product.get("nutriments", {})
            df_nutrients = pd.DataFrame(list(nutriments.items()), columns=["Nutriment", "Valeur"])
            df_nutrients = df_nutrients[df_nutrients["Nutriment"].str.contains("_100g")]
            df_nutrients["Nutriment"] = (
                df_nutrients["Nutriment"]
                .str.replace("_100g", "")
                .str.replace("_", " ")
                .str.capitalize()
            )
            df_nutrients["Valeur"] = df_nutrients["Valeur"].astype(float).round(1)
            st.table(df_nutrients)

        # ✅ Additional Information
        with st.expander("🔗 Plus d'informations"):
            st.write(f"**🔗 [Lien OpenFoodFacts]({product.get('url', 'N/A')})**")

        # ✅ Save JSON Button
        json_data = json.dumps(product, indent=4)
        st.download_button(
            label="💾 Télécharger les données du produit (JSON)",
            file_name=f"product_{barcode_data}.json",
            mime="application/json",
            data=json_data
        )
    else:
        col2.error("❌ Produit non trouvé.")

cap.release()
cv2.destroyAllWindows()

