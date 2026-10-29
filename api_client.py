
import requests

BASE_URL = "https://dummyjson.com"
REQUEST_TIMEOUT = 10
MAX_QUERY_LENGTH = 200


def search_products(query: str) -> dict:
    """Search products using the DummyJSON API."""

    # 1. Validate input type
    if not isinstance(query, str):
        return {
            "success": False,
            "error": "Product search query must be a string."
        }

    # 2. Remove surrounding whitespace
    query = query.strip()

    # 3. Reject empty input
    if not query:
        return {
            "success": False,
            "error": "Product search query cannot be empty."
        }

    # 4. Limit input length
    if len(query) > MAX_QUERY_LENGTH:
        return {
            "success": False,
            "error": "Product search query is too long."
        }

    # 5. Call external API
    try:
        response = requests.get(
            f"{BASE_URL}/products/search",
            params={"q": query},
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        # 6. Validate JSON response
        try:
            data = response.json()
        except ValueError:
            return {
                "success": False,
                "error": "Product API returned an invalid response."
            }

        # 7. Validate response structure
        if not isinstance(data, dict):
            return {
                "success": False,
                "error": "Product API returned an unexpected response."
            }

        products = data.get("products")

        if not isinstance(products, list):
            return {
                "success": False,
                "error": "Product API returned an unexpected product list."
            }

        return {
            "success": True,
            "data": data
        }

    except requests.Timeout:
        return {
            "success": False,
            "error": "Product API timed out."
        }

    except requests.RequestException:
        return {
            "success": False,
            "error": "Product API request failed."
        }
