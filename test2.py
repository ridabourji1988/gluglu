from openfoodfacts import API, APIVersion, Country, Environment, Flavor
from colorama import Fore, Style, init
import emoji

# Initialize colorama
init(autoreset=True)

# Initialize the API object
api = API(
    user_agent="MyAwesomeApp/1.0",
    country=Country.world,
    flavor=Flavor.off,
    version=APIVersion.v2,
    environment=Environment.org,
)

def get_product_details(barcode):
    """
    Get product details by barcode
    :param barcode: The barcode of the product to search for
    :return: Product details if found, otherwise None
    """
    product = api.product.get(barcode)
    return product

def search_products(query, page=1, page_size=20):
    """
    Search for products using a query
    :param query: The search query
    :param page: The page number (default is 1)
    :param page_size: The number of products per page (default is 20)
    :return: List of products found
    """
    products = api.product.text_search(query, page=page, page_size=page_size)
    return products["products"]

def print_product_details(product):
    """
    Print product details
    :param product: The product details to print
    """
    print(emoji.emojize(f"{Fore.GREEN}Product Name: {Fore.RESET}{product.get('product_name', 'N/A')} :package:"))
    print(emoji.emojize(f"{Fore.GREEN}Barcode: {Fore.RESET}{product.get('code', 'N/A')} :bar_chart:"))
    print(emoji.emojize(f"{Fore.GREEN}Brands: {Fore.RESET}{product.get('brands', 'N/A')} :label:"))
    print(emoji.emojize(f"{Fore.GREEN}Categories: {Fore.RESET}{product.get('categories', 'N/A')} :bookmark_tabs:"))
    print(emoji.emojize(f"{Fore.GREEN}Ingredients: {Fore.RESET}{product.get('ingredients_text', 'N/A')} :leafy_green:"))
    print(emoji.emojize(f"{Fore.GREEN}Nutriments: {Fore.RESET}{product.get('nutriments', 'N/A')} :pie:"))
    print(emoji.emojize(f"{Fore.GREEN}Image URL: {Fore.RESET}{product.get('image_url', 'N/A')} :frame_with_picture:"))
    print(emoji.emojize(f"{Fore.GREEN}URL: {Fore.RESET}{product.get('url', 'N/A')} :link:"))
    print(Fore.YELLOW + "Miscellaneous:")
    print(emoji.emojize(f" - Quantity: {Fore.RESET}{product.get('quantity', 'N/A')} :scales:"))
    print(emoji.emojize(f" - Packaging: {Fore.RESET}{product.get('packaging', 'N/A')} :package:"))
    print(emoji.emojize(f" - Labels: {Fore.RESET}{product.get('labels', 'N/A')} :label:"))
    print(Fore.YELLOW + "Tags:")
    print(emoji.emojize(f" - Categories Tags: {Fore.RESET}{product.get('categories_tags', 'N/A')} :bookmark_tabs:"))
    print(emoji.emojize(f" - Labels Tags: {Fore.RESET}{product.get('labels_tags', 'N/A')} :label:"))
    print(emoji.emojize(f" - Packaging Tags: {Fore.RESET}{product.get('packaging_tags', 'N/A')} :package:"))
    print(Fore.YELLOW + "Nutrition Info:")
    print(emoji.emojize(f" - Energy (kcal): {Fore.RESET}{product.get('nutriments', {}).get('energy-kcal_100g', 'N/A')} :fire:"))
    print(emoji.emojize(f" - Fat: {Fore.RESET}{product.get('nutriments', {}).get('fat_100g', 'N/A')} :meat_on_bone:"))
    print(emoji.emojize(f" - Saturated Fat: {Fore.RESET}{product.get('nutriments', {}).get('saturated-fat_100g', 'N/A')} :cut_of_meat:"))
    print(emoji.emojize(f" - Carbohydrates: {Fore.RESET}{product.get('nutriments', {}).get('carbohydrates_100g', 'N/A')} :bread:"))
    print(emoji.emojize(f" - Sugars: {Fore.RESET}{product.get('nutriments', {}).get('sugars_100g', 'N/A')} :chocolate_bar:"))
    print(emoji.emojize(f" - Fiber: {Fore.RESET}{product.get('nutriments', {}).get('fiber_100g', 'N/A')} :seedling:"))
    print(emoji.emojize(f" - Proteins: {Fore.RESET}{product.get('nutriments', {}).get('proteins_100g', 'N/A')} :poultry_leg:"))
    print(emoji.emojize(f" - Salt: {Fore.RESET}{product.get('nutriments', {}).get('salt_100g', 'N/A')} :salt:"))
    print(Fore.YELLOW + "Images Info:")
    print(emoji.emojize(f" - Image URL: {Fore.RESET}{product.get('image_url', 'N/A')} :frame_with_picture:"))
    print(Fore.YELLOW + "Eco-Score:")
    print(emoji.emojize(f" - Eco-Score: {Fore.RESET}{product.get('ecoscore_grade', 'N/A')} :earth_americas:"))
    print(Fore.YELLOW + "Metadata:")
    print(emoji.emojize(f" - Creator: {Fore.RESET}{product.get('creator', 'N/A')} :bust_in_silhouette:"))
    print(emoji.emojize(f" - Editors: {Fore.RESET}{product.get('editors', 'N/A')} :pencil:"))
    print(Fore.YELLOW + "Data Quality:")
    print(emoji.emojize(f" - Completeness: {Fore.RESET}{product.get('data_quality_tags', 'N/A')} :white_check_mark:"))
    print(Fore.YELLOW + "Knowledge Panels:")
    print(emoji.emojize(f" - Knowledge Panels: {Fore.RESET}{product.get('knowledge_panels', 'N/A')} :books:"))
    print(Fore.YELLOW + "Attribute Groups:")
    print(emoji.emojize(f" - Attribute Groups: {Fore.RESET}{product.get('attribute_groups', 'N/A')} :gear:"))
    print(Style.BRIGHT + "-" * 80)

if __name__ == "__main__":
    # print("Searching for products containing 'chocolate'...")
    # products = search_products("chocolate")
    # print(f"Found {len(products)} products.")

    # for product in products:
    #     print_product_details(product)

    print("Getting details for a specific product by barcode...")
    barcode = '737628064502'  # Example barcode
    product = get_product_details(barcode)
    if product:
        print_product_details(product)
    else:
        print("Product not found.")
