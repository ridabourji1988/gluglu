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
st.title("📸 Zxing Browser Barcode Scanner")
st.write("**No system dependencies.** Barcode scanning happens in the browser using Zxing, then automatically sends the code to Python.")

# We'll read any "?barcode=XXX" param from the URL
query_params = st.experimental_get_query_params()
barcode_data = query_params.get("barcode", [None])[0]

# Layout: left column for scanning, right column for product details
col1, col2 = st.columns([1, 1])

###########################################
# 3) LEFT COLUMN: Browser-based ZXing Scanner
###########################################
with col1:
    st.markdown("### Live Scanner (No Copy-Paste Needed)")
    st.info(
        "**Usage**:\n"
        "1) Allow camera access when prompted.\n"
        "2) Point your camera at a barcode.\n"
        "3) Once recognized, the app automatically refreshes with `?barcode=xxxx`.\n"
        "4) Product info is shown on the right."
    )

    # We define a custom HTML+JS block that:
    # - Loads Zxing from a CDN
    # - Accesses the camera
    # - On success, calls a hidden link /?barcode=DECODED_VALUE to reload the page
    #   with the recognized barcode in the URL param. Then Streamlit picks it up
    #   with st.experimental_get_query_params().

    components.html(
        """
        <!DOCTYPE html>
        <html>
          <head>
            <!-- ZXing library (ES module or UMD). Using the latest from CDN. -->
            <script src="https://cdn.jsdelivr.net/npm/@zxing/browser@latest"></script>
          </head>
          <body>
            <h4>Camera Preview</h4>
            <video id="video" width="300" height="200" style="border:1px solid gray"></video>
            <div id="log" style="margin-top:1em;color:green;">Initializing camera...</div>

            <script>
              // Access the ZXing Browser library
              const codeReader = new ZXing.BrowserMultiFormatReader();
              const videoElem = document.getElementById('video');
              const logElem = document.getElementById('log');

              // Start the camera and continuous decode
              codeReader
                .getVideoInputDevices()
                .then(videoInputDevices => {
                  // Select the first device (or you can find "environment" facing)
                  const deviceId = videoInputDevices.length > 0
                    ? videoInputDevices[0].deviceId
                    : null;

                  if (!deviceId) {
                    logElem.innerText = "No camera found.";
                    return;
                  }

                  // Start decoding from the camera
                  codeReader.decodeFromVideoDevice(deviceId, videoElem, (result, err) => {
                    if (result) {
                      const text = result.getText();
                      // Once we get a result, we build a new URL with "?barcode=text"
                      // Then force a reload so Streamlit sees the param
                      window.location.search = "barcode=" + encodeURIComponent(text);
                    }
                    if (err && !(err instanceof ZXing.NotFoundException)) {
                      // if it's just "NotFound", means no barcode in frame
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
        """,
        height=380,
        scrolling=False
    )

###########################################
# 4) RIGHT COLUMN: Show Product Info
###########################################
with col2:
    st.markdown("### Product Details")
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
        st.info("No barcode detected yet. Move a barcode into view on the left.")

