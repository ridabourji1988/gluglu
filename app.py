import streamlit as st
import requests
import pandas as pd
import json
import os
import streamlit.components.v1 as components

# Import your custom "barcode" module if you have it:
import barcode  # This is the module containing "get_product_details()"

# Ensure 'items' folder exists
if not os.path.exists("items"):
    os.makedirs("items")

# Streamlit Page Configuration
st.set_page_config(page_title="Scan Barcode", page_icon="📸", layout="wide")

st.title("📸 Scan Your Products")
st.write("Scan a barcode in your **browser** and retrieve product details instantly.")

# Layout: Two columns
col1, col2 = st.columns([1, 1])

# --- 1) Live Browser Scanner (HTML + JS) in col1 ---
with col1:
    st.markdown("### Live Barcode Scanner (via html5-qrcode)")
    st.info(
        "1. **Allow camera access** if prompted.\n"
        "2. Hold a barcode in front of your camera.\n"
        "3. **Copy** the scanned code and paste it into the text input on the right."
    )

    components.html(
        """
        <!DOCTYPE html>
        <html>
          <head>
            <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
          </head>
          <body>
            <div id="reader" style="width: 300px;"></div>
            <div id="result" style="margin-top: 1em; color: green;">Scan a barcode to see the result here.</div>

            <script>
              // Create the Html5Qrcode object
              const html5QrCode = new Html5Qrcode("reader");

              function onScanSuccess(decodedText, decodedResult) {
                // Show the result on the page
                document.getElementById('result').innerText = 
                  "Scanned Code: " + decodedText;
              }

              function onScanError(errorMessage) {
                // ignore errors for now
              }

              // Start scanning using the environment-facing camera (rear camera on mobile)
              html5QrCode.start(
                { facingMode: "environment" },
                {
                  fps: 10,  
                  qrbox: 250,
                  // Support typical 1D barcodes
                  formatsToSupport: [
                    Html5QrcodeSupportedFormats.EAN_13,
                    Html5QrcodeSupportedFormats.EAN_8,
                    Html5QrcodeSupportedFormats.UPC_A,
                    Html5QrcodeSupportedFormats.UPC_E,
                    Html5QrcodeSupportedFormats.CODE_39,
                    Html5QrcodeSupportedFormats.CODE_128,
                    Html5QrcodeSupportedFormats.ITF,
                    Html5QrcodeSupportedFormats.RSS_EXPANDED
                  ]
                },
                onScanSuccess,
                onScanError
              ).catch((err) => {
                document.getElementById('result').innerText = 
                  "Camera access error: " + err;
              });
            </script>
          </body>
        </html>
        """,
        height=500,
        scrolling=False
    )

# --- 2) Paste Barcode & Retrieve Product ---
with col2:
    st.markdown("### Paste the Barcode Here")
    barcode_data = st.text_input("Scanned Barcode")

    if barcode_data:
        st.success(f"**Barcode Detected:** `{barcode_data}`")

        # Fetch product details
        # Instead of calling the OpenFoodFacts API directly, 
        # we use your custom "barcode" module's function:
        product = barcode.get_product_details(barcode_data)

        if product:
            # Display product image
            st.image(product.get("image_url", "https://via.placeholder.com/150"), width=250)

            # Collect allergens from "attribute_groups"
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
                st.markdown("**Allergens:** " + " | ".join(allergens), unsafe_allow_html=True)

            # Ingredients
            ingredients_text = product.get("ingredients_text", "Ingredients not available.")
            with st.expander("📝 Ingredients"):
                formatted_ingredients = "- " + "\n- ".join(ingredients_text.split(", "))
                st.markdown(formatted_ingredients)

            # Nutritional Info
            with st.expander("Nutritional Information"):
                nutriments = product.get("nutriments", {})
                df_nutrients = pd.DataFrame(list(nutriments.items()), columns=["Nutrient", "Value"])
                df_nutrients = df_nutrients[df_nutrients["Nutrient"].str.contains("_100g")]
                df_nutrients["Nutrient"] = (
                    df_nutrients["Nutrient"]
                    .str.replace("_100g", "")
                    .str.replace("_", " ")
                    .str.capitalize()
                )
                # Convert to float if possible
                def to_float(x):
                    try:
                        return float(x)
                    except:
                        return x
                df_nutrients["Value"] = df_nutrients["Value"].apply(to_float)
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
            st.error("❌ Product not found.")
    else:
        st.warning("Awaiting barcode input... Copy the scanned code from the left panel.")

