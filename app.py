import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Browser Barcode Scanner", page_icon="📸", layout="wide")

st.title("📸 Browser-Based Barcode Scanner")
st.write("""
**No Python barcode libraries needed!**  
This uses [html5-qrcode](https://github.com/mebjas/html5-qrcode) **in the browser** to scan barcodes from your camera.  
Then you can **paste** the scanned code into the text box below, and we’ll look it up on OpenFoodFacts.
""")

#########################
# 1) Client-Side Scanner
#########################
# The camera feed and scanning happen entirely in the browser using HTML + JS.
# It supports many 1D barcode formats (EAN, UPC, CODE_39, CODE_128, etc.).
# We display the scanning widget in an iframe-like area (components.html).

components.html(
    """
    <!DOCTYPE html>
    <html>
      <head>
        <!-- Load html5-qrcode library from CDN -->
        <script src="https://unpkg.com/html5-qrcode" type="text/javascript"></script>
      </head>
      <body>
        <h3>Live Barcode Scanner</h3>
        <div id="reader" style="width: 300px;"></div>
        <div id="result" style="margin-top: 1em; color: green;">Scan a barcode to see the result here.</div>

        <script>
          // Create the Html5Qrcode object
          const html5QrCode = new Html5Qrcode("reader");

          // Callback when a successful scan occurs
          function onScanSuccess(decodedText, decodedResult) {
            // Show the result on the page
            document.getElementById('result').innerText = 
              "Scanned Code: " + decodedText;
          }

          // Callback for scan errors or in-progress scanning
          function onScanError(errorMessage) {
            // You could log errors for debugging
          }

          // Start scanning using camera
          html5QrCode.start(
            { facingMode: "environment" }, // Or "user" for front camera
            {
              fps: 10,  // scans per second
              qrbox: 250,
              // Add supported formats for typical 1D barcodes:
              formatsToSupport: [
                Html5QrcodeSupportedFormats.EAN_13,
                Html5QrcodeSupportedFormats.EAN_8,
                Html5QrcodeSupportedFormats.UPC_A,
                Html5QrcodeSupportedFormats.UPC_E,
                Html5QrcodeSupportedFormats.CODE_39,
                Html5QrcodeSupportedFormats.CODE_128,
                Html5QrcodeSupportedFormats.ITF,      // Interleaved 2 of 5
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
    height=600,  # Adjust height to your liking
    scrolling=False
)

################################
# 2) Paste the Barcode into Python
################################
st.subheader("Enter the Barcode You Scanned")
barcode_input = st.text_input("Barcode")

if barcode_input:
    st.success(f"**You entered**: `{barcode_input}`")

    # 3) Look up the product on OpenFoodFacts
    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode_input}.json"
    resp = requests.get(url).json()
    if "product" in resp:
        product = resp["product"]
        st.write("### Product Found:", product.get("product_name", "Unnamed Product"))

        # Show product image if available
        st.image(product.get("image_url", "https://via.placeholder.com/150"), width=200)

        # Allergens
        allergens = product.get("allergens", "No allergens listed.")
        st.markdown(f"**Allergens:** {allergens}")

        # Ingredients
        ingredients_text = product.get("ingredients_text", "Ingredients not available.")
        with st.expander("📝 Ingredients"):
            st.write(ingredients_text)

        # Nutritional Info
        nutriments = product.get("nutriments", {})
        if nutriments:
            st.subheader("Nutritional Information per 100g")
            df = pd.DataFrame(list(nutriments.items()), columns=["Key", "Value"])
            df = df[df["Key"].str.endswith("_100g")]
            df["Key"] = df["Key"].str.replace("_100g", "")
            st.table(df)
        else:
            st.info("No nutritional info found.")

        # Additional Info
        st.write("**OpenFoodFacts URL**:", product.get("url", "N/A"))
    else:
        st.error("❌ Product not found on OpenFoodFacts. Double-check the barcode!")
