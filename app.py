import streamlit as st
import requests
import pandas as pd
import json
import os
import streamlit.components.v1 as components

###############################################
# 1) Utility Function: Fetch Product from OFF #
###############################################
def get_product_details(barcode_data):
    """
    Fetch product details from OpenFoodFacts using 'barcode_data'.
    Returns the 'product' dict if found, else None.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_data}.json"
    resp = requests.get(url).json()
    if "product" in resp:
        return resp["product"]
    return None

################################
# 2) Basic Setup for Streamlit #
################################
# Ensure 'items' folder exists
if not os.path.exists("items"):
    os.makedirs("items")

st.set_page_config(page_title="Scan Barcode", page_icon="📸", layout="wide")
st.title("📸 Scan Your Products")
st.write("Scan a barcode in your **browser** and retrieve product details instantly.")

# Two columns: left for scanning, right for results
col1, col2 = st.columns([1, 1])

#############################################
# 3) LEFT COLUMN: Live Browser Barcode Scan #
#############################################
with col1:
    st.markdown("### Live Barcode Scanner (via html5-qrcode)")
    st.info(
        "**How to Use**:\n"
        "1) Allow camera access when prompted.\n"
        "2) Point your camera at a 1D barcode.\n"
        "3) Copy the detected barcode from below.\n"
        "4) Paste it into the text field on the right."
    )

    # Embedding html5-qrcode in an iframe-like component
    components.html(
        """
        <!DOCTYPE html>
        <html>
          <head>
            <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
          </head>
          <body>
            <div id="reader" style="width: 300px;"></div>
            <div id="result" style="margin-top: 1em; color: green;">
              Point the camera at a barcode...
            </div>

            <script>
              // Create the Html5Qrcode object
              const html5QrCode = new Html5Qrcode("reader");

              function onScanSuccess(decodedText, decodedResult) {
                document.getElementById('result').innerText =
                  "Scanned Code: " + decodedText;
              }

              function onScanError(errorMessage) {
                // We can ignore errors for a typical use-case
              }

              // Start scanning using environment-facing camera
              html5QrCode.start(
                { facingMode: "environment" },
                {
                  fps: 10,  
                  qrbox: 250,
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

################################################
# 4) RIGHT COLUMN: Paste Barcode & Show Result #
################################################
with col2:
    st.markdown("### Paste the Barcode Here")
    barcode_data = st.text_input("Scanned Barcode")

    if barcode_data:
        st.success(f"**Barcode Detected:** `{barcode_data}`")

        # 4A) Fetch product details from OFF
        product = get_product_details(barcode_data)

        if product:
            # 4B) Display product image
            col2.image(product.get("image_url", "https://via.placeholder.com/150"), width=250)

            # 4C) Extract allergens from "attribute_groups"
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

            if allergens:
                st.markdown("**Allergens:** " + " | ".join(allergens), unsafe_allow_html=True)

            # 4D) Ingredients Section
            ingredients_text = product.get("ingredients_text", "Ingredients not available.")
            with st.expander("📝 Ingredients"):
                formatted_ingredients = "- " + "\n- ".join(ingredients_text.split(", "))
                st.markdown(formatted_ingredients)

            # 4E) Nutritional Information
            with st.expander("Nutritional Information"):
                nutriments = product.get("nutriments", {})
                df_nutrients = pd.DataFrame(list(nutriments.items()), columns=["Nutrient", "Value"])
                # Filter for keys that contain "_100g"
                df_nutrients = df_nutrients[df_nutrients["Nutrient"].str.contains("_100g")]

                # Clean up key names
                df_nutrients["Nutrient"] = (
                    df_nutrients["Nutrient"]
                    .str.replace("_100g", "")
                    .str.replace("_", " ")
                    .str.capitalize()
                )
                # Convert numeric strings to floats, ignoring errors
                def try_float(x):
                    try:
                        return float(x)
                    except:
                        return x
                df_nutrients["Value"] = df_nutrients["Value"].apply(try_float)

                st.table(df_nutrients)

            with st.expander("Additional Information"):
                off_url = product.get('url', 'N/A')
                st.write(f"**[OpenFoodFacts URL]({off_url})**")

            # 4F) Save JSON Button
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
            st.error("❌ Product not found. Double-check the barcode!")
    else:
        st.warning("Awaiting barcode input... Copy the scanned code from the left panel.")
