import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import json
import os

###########################################
# 1) Utility: Fetch product from OpenFoodFacts
###########################################
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

###########################################
# 2) Basic Setup for Streamlit
###########################################
if not os.path.exists("items"):
    os.makedirs("items")

st.set_page_config(page_title="Zxing Browser Barcode", page_icon="📸", layout="wide")
st.title("📸 Zxing Browser Barcode Scanner - iFrame Camera Fix")

st.markdown("""
This example uses an **iframe** with explicit camera permissions. If you're on
Streamlit Cloud (HTTPS) and your browser settings allow it, you'll be prompted
to enable the camera. Once a barcode is detected, the URL is updated with
**?barcode=XXXXX** automatically, and the product info is displayed below.
""")

query_params = st.query_params
barcode_data = query_params.get("barcode", [None])[0]

# Layout: left column for scanning, right column for product details
col1, col2 = st.columns([1, 1])

###########################################
# 3) LEFT COLUMN: Iframe with Zxing & Camera Permissions
###########################################
with col1:
    st.subheader("Live Scanner (No Copy-Paste)")
    st.info(
        "**Usage**:\n"
        "1) Approve camera access when prompted.\n"
        "2) Show a barcode to the camera.\n"
        "3) Once recognized, `?barcode=CODE` is appended to the URL.\n"
        "4) Right column shows the product info automatically."
    )

    # We embed an <iframe> that explicitly sets `allow="camera; microphone"`.
    # Inside that iframe, we load a minimal HTML page that:
    # 1) Includes Zxing from a CDN.
    # 2) Accesses the camera.
    # 3) On success, sets window.parent.location.search = "?barcode=XXXX"
    #    so the parent page updates the query param, re-runs Streamlit with the code.

    html_content = """
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://cdn.jsdelivr.net/npm/@zxing/browser@latest"></script>
        <style>
          body { margin: 0; padding: 0; }
          video { border: 1px solid #999; }
          #log { margin-top: 1em; color: green; }
        </style>
      </head>
      <body>
        <h4 style="margin:0.5em;">Camera Preview</h4>
        <video id="video" width="300" height="200"></video>
        <div id="log">Initializing camera...</div>

        <script>
          const codeReader = new ZXing.BrowserMultiFormatReader();
          const videoElem = document.getElementById('video');
          const logElem   = document.getElementById('log');

          codeReader.getVideoInputDevices().then(videoInputDevices => {
            if (videoInputDevices.length === 0) {
              logElem.innerText = "No camera found.";
              return;
            }
            // Use the first camera device
            const deviceId = videoInputDevices[0].deviceId;

            codeReader.decodeFromVideoDevice(deviceId, videoElem, (result, err) => {
              if (result) {
                const text = result.getText();
                // On successful scan, update parent's URL with ?barcode=....
                window.parent.location.search = "barcode=" + encodeURIComponent(text);
              }
              if (err && !(err instanceof ZXing.NotFoundException)) {
                console.error(err);
              }
            });
          })
          .catch(err => {
            logElem.innerText = "Camera error: " + err;
          });
        </script>
      </body>
    </html>
    """

    # Build an iframe that sets allow="camera; microphone"
    iframe_code = f"""
    <iframe 
      srcdoc="{html_content.replace('"', '&quot;')}"
      width="320" 
      height="350"
      allow="camera; microphone"
      style="border:none;"
    >
    </iframe>
    """

    components.html(iframe_code, height=400, scrolling=False)

###########################################
# 4) RIGHT COLUMN: Show Product Info
###########################################
with col2:
    st.subheader("Product Details")

    if barcode_data:
        st.success(f"**Barcode Detected:** `{barcode_data}`")
        product = get_product_details(barcode_data)

        if product:
            # Display product image
            st.image(product.get("image_url", "https://via.placeholder.com/150"), width=200)

            # Process allergens from attribute_groups
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

            # Ingredients
            ingredients_text = product.get("ingredients_text", "Ingredients not available.")
            st.write("#### Ingredients")
            st.write(ingredients_text)

            # Nutritional Info
            st.write("#### Nutritional Info (per 100g)")
            nutriments = product.get("nutriments", {})
            df_nutrients = pd.DataFrame(list(nutriments.items()), columns=["Nutrient", "Value"])
            df_nutrients = df_nutrients[df_nutrients["Nutrient"].str.contains("_100g")]
            df_nutrients["Nutrient"] = (
                df_nutrients["Nutrient"]
                .str.replace("_100g", "")
                .str.replace("_", " ")
                .str.capitalize()
            )
            def try_float(x):
                try:
                    return float(x)
                except:
                    return x
            df_nutrients["Value"] = df_nutrients["Value"].apply(try_float)
            st.table(df_nutrients)

            # Additional Info
            st.write("#### Additional Info")
            off_url = product.get("url", "")
            if off_url:
                st.write(f"[OpenFoodFacts URL]({off_url})")

            # Save JSON
            json_data = json.dumps(product, indent=4)
            file_path = os.path.join("items", f"product_{barcode_data}.json")
            with open(file_path, "w") as f:
                f.write(json_data)

            st.download_button(
                label="💾 Save as JSON",
                file_name=f"product_{barcode_data}.json",
                mime="application/json",
                data=json_data
            )
        else:
            st.error("❌ Product not found on OpenFoodFacts.")
    else:
        st.info("No barcode detected yet. Show a barcode to the camera on the left.")


