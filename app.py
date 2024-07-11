# streamlit_app.py
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)
print("sys.path:", sys.path)

from colorama import Fore, Style, init
import streamlit as st
import requests
from colorama import Fore, Style, init
import emoji
import re
import cv2
from pyzbar.pyzbar import decode
import numpy as np

# Initialize colorama
init(autoreset=True)

BASE_URL = "https://fr.openfoodfacts.org"

def get_product_details(barcode):
    url = f"{BASE_URL}/api/v3/product/{barcode}.json"
    params = {
        'fields': 'product_name,code,brands,categories,ingredients_text,nutriments,image_url,url,quantity,packaging,labels,categories_tags,labels_tags,packaging_tags,nutriments,ecoscore_grade,creator,editors,data_quality_tags,knowledge_panels,attribute_groups',
        'lc': 'fr', 'cc': 'fr'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get('product', None)
    else:
        return None

def search_products(query, page=1, page_size=20):
    url = f"{BASE_URL}/cgi/search.pl"
    params = {
        'search_terms': query, 'page': page, 'page_size': page_size,
        'json': 1, 'lc': 'fr', 'cc': 'fr',
        'fields': 'product_name,code,brands,categories,ingredients_text,nutriments,image_url,url,quantity,packaging,labels,categories_tags,labels_tags,packaging_tags,nutriments,ecoscore_grade,creator,editors,data_quality_tags,knowledge_panels,attribute_groups'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("products", [])
    else:
        return []

def format_nutriments(nutriments):
    formatted_nutriments = []
    for key, value in nutriments.items():
        if isinstance(value, (int, float)) and key.endswith('_100g'):
            nutrient = key.replace('_100g', '').replace('_', ' ').capitalize()
            formatted_nutriments.append(f" - {nutrient}: {value} {nutriments.get(f'{key}_unit', '')}")
    return '\n'.join(formatted_nutriments)

def format_list(items):
    return '\n'.join([f" - {item}" for item in items])

def format_dict(data):
    if isinstance(data, list):
        formatted_data = [format_dict(item) for item in data]
        return '\n'.join(formatted_data)
    elif isinstance(data, dict):
        formatted_data = []
        for key, value in data.items():
            formatted_key = key.replace('_', ' ').capitalize()
            if isinstance(value, dict):
                formatted_value = format_dict(value)
            elif isinstance(value, list):
                formatted_value = format_list(value)
            else:
                formatted_value = value
            formatted_data.append(f"{formatted_key}: {formatted_value}")
        return '\n'.join(formatted_data)
    else:
        return str(data)

def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext

def flatten_knowledge_panels(panels):
    flattened = []
    for panel in panels.values():
        for element in panel.get('elements', []):
            if element['element_type'] == 'text':
                flattened.append(clean_html(element['text_element']['html']))
            elif element['element_type'] == 'table':
                table = element['table_element']
                flattened.append(f"{table['title']}:")
                for row in table['rows']:
                    row_text = ", ".join([f"{cell['text']}" for cell in row['values']])
                    flattened.append(f"  - {row_text}")
    return "\n".join(flattened)

def print_product_details(product):
    st.write(emoji.emojize(f"**Nom du produit:** {product.get('product_name', 'N/A')} 📦"))
    st.write(emoji.emojize(f"**Code-barres:** {product.get('code', 'N/A')} 📊"))
    st.write(emoji.emojize(f"**Marques:** {product.get('brands', 'N/A')} 🏷️"))
    st.write(emoji.emojize(f"**Catégories:** {product.get('categories', 'N/A')} 📑"))
    st.write(emoji.emojize(f"**Ingrédients:** {product.get('ingredients_text', 'N/A')} 🥬"))
    
    st.write("**Allergènes:**")
    allergens = product.get('attribute_groups', [])
    for group in allergens:
        if group.get('id') == 'allergens':
            for attribute in group.get('attributes', []):
                title_text = attribute.get('title', 'N/A')
                if "Ne contient pas" in title_text:
                    title = f"{title_text}"
                elif "Présence inconnue" in title_text:
                    title = f"{title_text}"
                else:
                    title = f"{title_text}"
                st.write(emoji.emojize(f" - {title}"))

    st.write(emoji.emojize(f"**Nutriments:**\n{format_nutriments(product.get('nutriments', {}))}"))
    st.write(emoji.emojize(f"**URL de l'image:** {product.get('image_url', 'N/A')}"))
    st.write(emoji.emojize(f"**URL:** {product.get('url', 'N/A')} 🔗"))
    # st.write("**Divers:**")
    # st.write(emoji.emojize(f" - **Quantité:** {product.get('quantity', 'N/A')} :scales:"))
    # st.write(emoji.emojize(f" - **Emballage:** {product.get('packaging', 'N/A')} 📦"))
    # st.write(emoji.emojize(f" - **Étiquettes:** {product.get('labels', 'N/A')} 🏷️"))
    # st.write("**Tags:**")
    # st.write(emoji.emojize(f" - **Tags des catégories:** {format_list(product.get('categories_tags', []))} 📑"))
    # st.write(emoji.emojize(f" - **Tags des étiquettes:** {format_list(product.get('labels_tags', []))} 🏷️"))
    # st.write(emoji.emojize(f" - **Tags d'emballage:** {format_list(product.get('packaging_tags', []))} 📦"))
    # st.write("**Infos nutritionnelles:**")
    st.write(emoji.emojize(f" - **Énergie (kcal):** {product.get('nutriments', {}).get('energy-kcal_100g', 'N/A')} 🔥"))
    st.write(emoji.emojize(f" - **Graisse:** {product.get('nutriments', {}).get('fat_100g', 'N/A')} 🍖"))
    st.write(emoji.emojize(f" - **Graisses saturées:** {product.get('nutriments', {}).get('saturated-fat_100g', 'N/A')} 🥩"))
    st.write(emoji.emojize(f" - **Glucides:** {product.get('nutriments', {}).get('carbohydrates_100g', 'N/A')} 🍞"))
    st.write(emoji.emojize(f" - **Sucres:** {product.get('nutriments', {}).get('sugars_100g', 'N/A')} 🍫"))
    st.write(emoji.emojize(f" - **Fibres:** {product.get('nutriments', {}).get('fiber_100g', 'N/A')} 🌱"))
    st.write(emoji.emojize(f" - **Protéines:** {product.get('nutriments', {}).get('proteins_100g', 'N/A')} 🍗"))
    st.write(emoji.emojize(f" - **Sel:** {product.get('nutriments', {}).get('salt_100g', 'N/A')} 🧂"))

    st.write("**Groupes d'attributs:**")
    attribute_groups = product.get('attribute_groups', [])
    for group in attribute_groups:
        if group.get('id') != 'allergens':  # Skip allergens as it is already printed
            st.write(emoji.emojize(f"**Id:** {group.get('id', 'N/A')}\n**Name:** {group.get('name', 'N/A')} ⚙️"))
            st.write(format_list([f"{attr.get('title', 'N/A')}: {attr.get('description_short', 'N/A')}" for attr in group.get('attributes', [])]))
    st.write("-" * 80)



# Initialize session state
if 'scanning' not in st.session_state:
    st.session_state.scanning = False

def start_scanning():
    st.session_state.scanning = True

def stop_scanning():
    st.session_state.scanning = False

# Function to scan barcode using the webcam
def scan_barcode():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error("Cannot open webcam")
        return None

    barcode_data = None

    frame_placeholder = st.empty()

    while cap.isOpened() and st.session_state.scanning:
        ret, frame = cap.read()
        if not ret:
            st.error("Failed to capture frame from webcam")
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # Convert BGR to RGB for Streamlit display
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
                st.session_state.scanning = False
                cap.release()
                cv2.destroyAllWindows()
                return barcode_data

        frame_placeholder.image(frame_rgb, channels="RGB")

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
    if st.session_state.scanning:
        if st.button("Stop Scanning", key="stop_scanning"):
            stop_scanning()
        barcode = scan_barcode()
        if not barcode:
            st.error("Échec de la capture du code-barres.")
    else:
        if st.button("Start Scanning", key="start_scanning"):
            start_scanning()
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
