import streamlit as st
import cv2
import numpy as np
from pyzbar.pyzbar import decode

def scan_barcode():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Cannot open webcam")
        return None

    st.write("Scanning for barcode. The camera will stop automatically once a barcode is detected.")
    barcode_data = None

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to capture frame from webcam")
            break

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB for Streamlit display
        for barcode in decode(frame):
            barcode_data = barcode.data.decode('utf-8')
            pts = barcode.polygon
            if len(pts) > 4:
                hull = cv2.convexHull(np.array([pt for pt in pts], dtype=np.float32))
                hull = list(map(tuple, np.squeeze(hull)))
            else:
                hull = pts

            rect = barcode.rect
            cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 255, 255), 2)

            n = len(hull)
            for j in range(0, n):
                pt1 = (int(hull[j][0]), int(hull[j][1]))
                pt2 = (int(hull[(j + 1) % n][0]), int(hull[(j + 1) % n][1]))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

            x = int(barcode.rect.left)
            y = int(barcode.rect.top) - 10
            cv2.putText(frame, barcode_data, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)

            if barcode_data:
                st.write(f"Barcode detected: {barcode_data}")
                cap.release()
                cv2.destroyAllWindows()
                return barcode_data

        # Display the frame in Streamlit
        st.image(frame, channels="RGB")

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# Streamlit App
st.title("Product Information Scanner")

option = st.selectbox("Choisissez une option:", ["Saisir le code-barres manuellement", "Scanner le code-barres avec la webcam", "Rechercher par critère (e.g Gluten Free)"])

barcode = None  # Initialize barcode to None

if option == "Saisir le code-barres manuellement":
    barcode = st.text_input("Entrez le code-barres:")
elif option == "Scanner le code-barres avec la webcam":
    if st.button("Start Scanning"):
        barcode = scan_barcode()
        if not barcode:
            st.error("Échec de la capture du code-barres.")
elif option == "Rechercher par critère (e.g Gluten Free)":
    criteria = st.text_input("Entrez le critère de recherche:")
    if criteria:
        products = search_products(criteria)
        st.write(f"Found {len(products)} products.")
        for product in products:
            print_product_details(product)

if barcode:
    st.write(f"Obtention des détails pour {barcode}...")
    product = get_product_details(barcode)
    if product:
        print_product_details(product)
    else:
        st.error("Produit non trouvé.")
