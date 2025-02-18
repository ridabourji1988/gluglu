import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import json
import os

###########################################
# 1) Utility: Fetch product from OpenFoodFacts
###########################################
def fetch_product_details(barcode_data):
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

st.set_page_config(page_title="Zxing Live Barcode", page_icon="📸", layout="wide")

st.title("📸 Scan Your Products")
st.write("Scan a barcode via your **browser’s camera**—no file upload needed!")

# We'll read any "?barcode=XXX" from the URL
query_params = st.query_params
barcode_data = query_params.get("barcode", [None])[0]

# Two columns: left for scanning, right for product details
col1, col2 = st.columns([1, 1])

###########################################
# 3) LEFT COLUMN: Zxing in the Browser
###########################################
with col1:
    st.markdown("### Live Scanner (Zxing in the Browser)")
    st.info(
        "1) **Allow camera** when prompted.\n"
        "2) Point your camera at a barcode.\n"
        "3) When recognized, the page reloads with `?barcode=xxx`.\n"
        "4) See product details on the right automatically."
    )

    # We embed a snippet of HTML + JS that:
    # - Loads Zxing from a CDN
    # - Accesses the camera
    # - On success, sets window.location.search = "?barcode=..."
    zxing_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://cdn.jsdelivr.net/npm/@zxing/browser@latest"></script>
        <style>
          body { margin: 0; padding: 0; }
          #video { border: 1px solid #999; }
          #log { color: green; margin-top: 1em; }
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

          codeReader.getVideoInputDevices()
            .then((devices) => {
              if (devices.length === 0) {
                logElem.innerText = "No camera found.";
                return;
              }
              const deviceId = devices[0].deviceId;

              codeReader.decodeFromVideoDevice(deviceId, videoElem, (result, err) => {
                if (result) {
                  const text = result.getText();
                  // Reload page with ?barcode=...
                  window.location.search = "barcode=" + encodeURIComponent(text);
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

    # Wrap in an iframe with camera permissions
    iframe_code = f"""
    <iframe 
      srcdoc="{zxing_html.replace('"', '&quot;')}"
      width="320" 
      height="370"
      style="border:none;"
      allow="camera; microphone"
    ></iframe>
    """

    components.html(iframe_code, height=400, scrolling=False)

###########################################
# 4) RIGHT COLUMN: Show Product Details
###########################################
with col2:
    st.markdown("### Product Details")
    if barcode_data:
        st.success(f"**Barcode Detected:** `{barcode_data}`")

        product = fetch_product_details(barcode_data)

        if product:
            # Display product image
            col2.image(product.get("image_url", "https://via.placeholder.com/150"), width=250)

            # Extract & display allergens
            allergens = product.get("allergens", "No allergens listed.")
            col2.markdown(f"**Allergens:** {allergens}")

            # Ingredients Section
            ingredients_text = product.get("ingredients_text", "Ingredients not available.")
            with st.expander("📝 Ingredients"):
                formatted_ingredients = "- " + "\n- ".join(ingredients_text.split(", "))
                st.markdown(formatted_ingredients)

            # Nutritional Information
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
                def try_float(x):
                    try:
                        return float(x)
                    except:
                        return x
                df_nutrients["Value"] = df_nutrients["Value"].apply(try_float)
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
        st.warning("No barcode detected yet. Aim your camera at a barcode on the left.")


