import streamlit as st
import requests
import pandas as pd
import json
import os
import streamlit.components.v1 as components

##############################
# 1) get_product_details
##############################
def get_product_details(barcode_data):
    """
    Example: fetch from OpenFoodFacts or your own endpoint.
    Return a dict with:
      'image_url', 'attribute_groups', 'nutriments', 'ingredients_text', 'url', etc.
    """
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_data}.json"
    resp = requests.get(url).json()
    if "product" in resp:
        return resp["product"]
    return None

##############################
# 2) Basic Setup
##############################
if not os.path.exists("items"):
    os.makedirs("items")

st.set_page_config(page_title="Zxing Direct Camera", page_icon="📸", layout="wide")
st.title("📸 Zxing Scanner - No Iframe")
st.write("""
**If you’re on iOS Safari**:  
1) Make sure you're in **Safari** itself (not an in-app browser).  
2) Check camera permission in device settings.  
3) If it still won't prompt, try "Add to Home Screen" or test on a desktop/Android device to confirm everything works.
""")

# We'll parse "?barcode=..." from st.query_params
query_params = st.query_params
barcode_data = query_params.get("barcode", [None])[0]

##############################
# 3) Two Columns Layout
##############################
col1, col2 = st.columns([1,1])

##############################
# 4) LEFT: Directly Insert the Zxing JS
##############################
with col1:
    st.markdown("### Live Camera (No iFrame)")
    st.info(
        "1) **Allow camera** if prompted.\n"
        "2) Show a barcode.\n"
        "3) On success, `?barcode=CODE` updates in the URL.\n"
        "4) Check product details on the right."
    )

    # HTML that loads Zxing, uses camera, updates parent URL with "?barcode=..."
    # placed directly in the top-level of the HTML snippet
    zxing_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <script src="https://cdn.jsdelivr.net/npm/@zxing/browser@latest"></script>
        <style>
          body {
            margin: 0; padding: 0;
            background-color: #f8f9fa;
            font-family: sans-serif;
          }
          #video {
            border: 1px solid #ccc;
          }
        </style>
      </head>
      <body>
        <h4 style="margin:0.5em;">Camera Preview</h4>
        <video id="video" width="300" height="200"></video>
        <div id="log" style="margin-top:1em;color:green;">Initializing camera...</div>

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

              // Start decoding from video
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

    # Use components.html with allow="camera; microphone" 
    # so the top-level snippet can request camera
    components.html(
        zxing_html,
        height=400,
        scrolling=False
        # There's no direct argument to set "allow=..." in this call,
        # but Streamlit sets the top-level iframe. Usually this is enough.
        # If iOS Safari still blocks, see the 'Add to Home Screen' trick.
    )

##############################
# 5) RIGHT: Product Details
##############################
with col2:
    st.markdown("### Product Details")
    if barcode_data:
        st.success(f"**Barcode Detected:** `{barcode_data}`")
        product = get_product_details(barcode_data)
        if product:
            # Show image
            st.image(product.get("image_url", "https://via.placeholder.com/150"), width=200)

            # Collect allergens
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
            st.error("❌ Product not found.")
    else:
        st.info("No barcode detected yet. Show a barcode to the camera on the left.")
