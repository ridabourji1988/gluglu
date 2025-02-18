import streamlit as st
import streamlit.components.v1 as components
import requests
import pandas as pd
import json
import os

##############################
# 1) Product Detail Function #
##############################
def get_product_details(barcode_data):
    """
    Example: Fetch product details from OpenFoodFacts.
    Return a dictionary with the same keys you used in your expansions:
      'image_url', 'attribute_groups', 'nutriments', 'ingredients_text', 'url', etc.
    """
    # Query the OpenFoodFacts API
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_data}.json"
    resp = requests.get(url).json()

    if "product" in resp:
        return resp["product"]
    return None  # If not found or invalid

##############################
# 2) Basic Setup
##############################
if not os.path.exists("items"):
    os.makedirs("items")

st.set_page_config(page_title="Scan Barcode", page_icon="📸", layout="wide")
st.title("📸 Scan Your Products")
st.write("Scan a barcode in your browser and retrieve product details instantly.")

# Read any "?barcode=XXXX" param from the URL using st.query_params
query_params = st.query_params
barcode_data = query_params.get("barcode", [None])[0]  # Get first value or None

##############################
# 3) Two Columns
##############################
col1, col2 = st.columns([1, 1])

##############################
# 4) LEFT: Browser-Based Scanner
##############################
with col1:
    st.markdown("### Browser Scanner")
    st.info(
        "1. **Allow camera** access when prompted.\n"
        "2. Point a **barcode** at your camera.\n"
        "3. When detected, the page **reloads** with `?barcode=XXX`.\n"
        "4. See product details on the right.\n"
    )

    # We'll embed the Zxing code in an iframe, with camera permissions
    # On successful scan, we set window.parent.location.search = "?barcode=thecode"
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
            // Use first camera device
            const deviceId = videoInputDevices[0].deviceId;
            codeReader.decodeFromVideoDevice(deviceId, videoElem, (result, err) => {
              if (result) {
                const text = result.getText();
                // On success, reload with ?barcode=text
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

    iframe_code = f"""
    <iframe 
      srcdoc="{html_content.replace('"', '&quot;')}"
      width="320" 
      height="370"
      allow="camera; microphone"
      style="border:none;"
    ></iframe>
    """

    components.html(iframe_code, height=400, scrolling=False)

##############################
# 5) RIGHT: Product Details
##############################
with col2:
    st.markdown("### Product Details")
    if barcode_data:
        st.success(f"**Barcode Detected:** `{barcode_data}`")

        # Fetch product details
        product = get_product_details(barcode_data)

        if product:
            # 5A) Product Image
            st.image(product.get("image_url", "https://via.placeholder.com/150"), width=250)

            # 5B) Allergens from attribute_groups
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

            # Display allergen tags if any
            if allergens:
                st.markdown("**Allergens:** " + " | ".join(allergens), unsafe_allow_html=True)

            # 5C) Ingredients Section
            ingredients_text = product.get("ingredients_text", "Ingredients not available.")
            with st.expander("📝 Ingredients"):
                formatted_ingredients = "- " + "\n- ".join(ingredients_text.split(", "))
                st.markdown(formatted_ingredients)

            # 5D) Nutritional Information
            with st.expander("Nutritional Information"):
                nutriments = product.get("nutriments", {})
                df_nutrients = pd.DataFrame(list(nutriments.items()), columns=["Nutrient", "Value"])
                # Filter for keys with "_100g"
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

            # 5E) Additional Info
            with st.expander("Additional Information"):
                st.write(f"**[OpenFoodFacts URL]({product.get('url', 'N/A')})**")

            # 5F) Save JSON Button
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


