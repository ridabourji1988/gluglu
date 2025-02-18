import requests
from colorama import Fore, Style, init
import emoji
import re
import cv2
from pyzbar.pyzbar import decode
import numpy as np  # Import numpy

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
    print(emoji.emojize(f"{Fore.GREEN}Nom du produit: {Fore.RESET}{product.get('product_name', 'N/A')} 📦"))
    print(emoji.emojize(f"{Fore.GREEN}Code-barres: {Fore.RESET}{product.get('code', 'N/A')} 📊"))
    print(emoji.emojize(f"{Fore.GREEN}Marques: {Fore.RESET}{product.get('brands', 'N/A')} 🏷️"))
    print(emoji.emojize(f"{Fore.GREEN}Catégories: {Fore.RESET}{product.get('categories', 'N/A')} 📑"))
    print(emoji.emojize(f"{Fore.GREEN}Ingrédients: {Fore.RESET}{product.get('ingredients_text', 'N/A')} 🥬"))
    
    # Allergens Section
 


    print(Fore.YELLOW + "Allergènes:" + Style.RESET_ALL)
    allergens = product.get('attribute_groups', [])
    for group in allergens:
        if group.get('id') == 'allergens':
            for attribute in group.get('attributes', []):
                title_text = attribute.get('title', 'N/A')
                if "Ne contient pas" in title_text:
                    title = Fore.GREEN + title_text + Style.RESET_ALL
                elif "Présence inconnue" in title_text:
                    title = Fore.WHITE + title_text + Style.RESET_ALL
                else:
                    title = Fore.RED + title_text + Style.RESET_ALL
                print(emoji.emojize(f" - {title}"))

    # Example of further print statements in your script
    print(emoji.emojize(f"{Fore.GREEN}Nutriments: {Fore.RESET}\n{format_nutriments(product.get('nutriments', {}))}"))
    print(emoji.emojize(f"{Fore.GREEN}URL de l'image: {Fore.RESET}{product.get('image_url', 'N/A')}"))
    
    print(emoji.emojize(f"{Fore.GREEN}Nutriments: {Fore.RESET}\n{format_nutriments(product.get('nutriments', {}))} 🥧"))
    print(emoji.emojize(f"{Fore.GREEN}URL de l'image: {Fore.RESET}{product.get('image_url', 'N/A')} :frame_with_picture:"))
    print(emoji.emojize(f"{Fore.GREEN}URL: {Fore.RESET}{product.get('url', 'N/A')} 🔗"))
    print(Fore.YELLOW + "Divers:")
    print(emoji.emojize(f" - Quantité: {Fore.RESET}{product.get('quantity', 'N/A')} :scales:"))
    print(emoji.emojize(f" - Emballage: {Fore.RESET}{product.get('packaging', 'N/A')} 📦"))
    print(emoji.emojize(f" - Étiquettes: {Fore.RESET}{product.get('labels', 'N/A')} 🏷️"))
    print(Fore.YELLOW + "Tags:")
    print(emoji.emojize(f" - Tags des catégories: {Fore.RESET}{format_list(product.get('categories_tags', []))} 📑"))
    print(emoji.emojize(f" - Tags des étiquettes: {Fore.RESET}{format_list(product.get('labels_tags', []))} 🏷️"))
    print(emoji.emojize(f" - Tags d'emballage: {Fore.RESET}{format_list(product.get('packaging_tags', []))} 📦"))
    print(Fore.YELLOW + "Infos nutritionnelles:")
    print(emoji.emojize(f" - Énergie (kcal): {Fore.RESET}{product.get('nutriments', {}).get('energy-kcal_100g', 'N/A')} 🔥"))
    print(emoji.emojize(f" - Graisse: {Fore.RESET}{product.get('nutriments', {}).get('fat_100g', 'N/A')} 🍖"))
    print(emoji.emojize(f" - Graisses saturées: {Fore.RESET}{product.get('nutriments', {}).get('saturated-fat_100g', 'N/A')} 🥩"))
    print(emoji.emojize(f" - Glucides: {Fore.RESET}{product.get('nutriments', {}).get('carbohydrates_100g', 'N/A')} 🍞"))
    print(emoji.emojize(f" - Sucres: {Fore.RESET}{product.get('nutriments', {}).get('sugars_100g', 'N/A')} 🍫"))
    print(emoji.emojize(f" - Fibres: {Fore.RESET}{product.get('nutriments', {}).get('fiber_100g', 'N/A')} 🌱"))
    print(emoji.emojize(f" - Protéines: {Fore.RESET}{product.get('nutriments', {}).get('proteins_100g', 'N/A')} 🍗"))
    print(emoji.emojize(f" - Sel: {Fore.RESET}{product.get('nutriments', {}).get('salt_100g', 'N/A')} 🧂"))

    print(Fore.YELLOW + "Groupes d'attributs:")
    attribute_groups = product.get('attribute_groups', [])
    for group in attribute_groups:
        if group.get('id') != 'allergens':  # Skip allergens as it is already printed
            print(emoji.emojize(f"Id: {group.get('id', 'N/A')}\nName: {group.get('name', 'N/A')} ⚙️"))
            print(format_list([f"{attr.get('title', 'N/A')}: {attr.get('description_short', 'N/A')}" for attr in group.get('attributes', [])]))
    print(Style.BRIGHT + "-" * 80)



def scan_barcode():
    cap = cv2.VideoCapture(0)
    barcode_data = None

    print("Scanning for barcode. The camera will stop automatically once a barcode is detected.")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        for barcode in decode(frame):
            barcode_data = barcode.data.decode('utf-8')
            pts = barcode.polygon
            if len(pts) > 4:
                hull = cv2.convexHull(np.array([pt for pt in pts], dtype=np.float32))
                hull = list(map(tuple, np.squeeze(hull)))
            else:
                hull = pts

            # Draw the yellow rectangle around the barcode
            rect = barcode.rect
            cv2.rectangle(frame, (rect.left, rect.top), (rect.left + rect.width, rect.top + rect.height), (0, 255, 255), 2)

            # Draw the green convex hull
            n = len(hull)
            for j in range(0, n):
                pt1 = (int(hull[j][0]), int(hull[j][1]))
                pt2 = (int(hull[(j + 1) % n][0]), int(hull[(j + 1) % n][1]))
                cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

            # Display barcode data
            x = int(barcode.rect.left)
            y = int(barcode.rect.top) - 10
            cv2.putText(frame, barcode_data, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 255), 2)

            # Stop the camera once a barcode is detected
            if barcode_data:
                print(f"Barcode detected: {barcode_data}")
                cv2.imshow('Barcode Scanner', frame)
                cv2.waitKey(1000)  # Display the final frame for 1 second before closing
                cap.release()
                cv2.destroyAllWindows()
                return barcode_data

        cv2.imshow('Barcode Scanner', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None



if __name__ == "__main__":
    print("Choisissez une option:")
    print("1. Saisir le code-barres manuellement")
    print("2. Scanner le code-barres avec la webcam")
    print("3. Rechercher par critère (e.g Gluten Free)")
    choice = input("Entrez 1, 2 ou 3: ")

    barcode = None  # Initialize barcode to None

    if choice == '1':
        barcode = input("Entrez le code-barres: ")
    elif choice == '2':
        barcode = scan_barcode()
        if not barcode:
            print("Échec de la capture du code-barres.")
            exit()
    elif choice == '3':
        criteria = input("Entrez le critère de recherche: ")
        products = search_products(criteria)
        print(f"Found {len(products)} products.")

        for product in products:
            print_product_details(product)
        exit()  # Exit after displaying the search results
    else:
        print("Choix invalide.")
        exit()

    print(f"Obtention des détails pour {barcode}...")
    product = get_product_details(barcode)

    if product:
        print_product_details(product)
    else:
        print("Produit non trouvé.")