from openfoodfacts import API, APIVersion, Country, Environment, Flavor

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
    print("Product Name:", product.get('product_name', 'N/A'))
    print("Barcode:", product.get('code', 'N/A'))
    print("Brands:", product.get('brands', 'N/A'))
    print("Categories:", product.get('categories', 'N/A'))
    print("Ingredients:", product.get('ingredients_text', 'N/A'))
    print("Nutriments:", product.get('nutriments', 'N/A'))
    print("Image URL:", product.get('image_url', 'N/A'))
    print("URL:", product.get('url', 'N/A'))
    print("-" * 80)

if __name__ == "__main__":
    print("Searching for products containing 'chocolate'...")
    products = search_products("gluten free")
    print(f"Found {len(products)} products.")

    for product in products:
        print_product_details(product)

    # print("Getting details for a specific product by barcode...")
    # barcode = '3029330004233'  # Example barcode
    # product = get_product_details(barcode)
    # if product:
    #     print_product_details(product)
    else:
        print("Product not found.")
