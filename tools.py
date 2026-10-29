
from langchain.tools import tool

from api_client import search_products
from rag import retrieve_knowledge



@tool
def product_search(product_name: str) -> dict:
    """
    Search the product catalog and return
    current product information.
    """

    if not isinstance(product_name, str):
        return {
            "success": False,
            "error": "Product name must be a string."
        }

    product_name = product_name.strip()

    if not product_name:
        return {
            "success": False,
            "error": "Product name cannot be empty."
        }

    if len(product_name) > 200:
        return {
            "success": False,
            "error": "Product name cannot exceed 200 characters."
        }

    result = search_products(product_name)

    if not result["success"]:
        return result

    data = result["data"]
    products = data.get("products", [])

    if not products:
        return {
            "success": True,
            "found": False,
            "message": "Product not found."
        }

    product = products[0]

    return {
        "success": True,
        "found": True,
        "product": {
            "id": product.get("id"),
            "name": product.get("title"),
            "price": product.get("price"),
            "stock": product.get("stock"),
            "rating": product.get("rating")
        }
    }



@tool
def knowledge_search(question: str) -> dict:
    """
    Search the internal knowledge base for relevant
    information about company policies, returns,
    shipping, warranty, and product guidance.

    Use this tool when answering questions that require
    information from the internal knowledge base.
    """

    try:
        results = retrieve_knowledge(question, limit=4)

        return {
            "success": True,
            "found": bool(results),
            "results": results
        }

    except ValueError as exc:
        return {
            "success": False,
            "error": str(exc),
            "results": []
        }

    except Exception:
        # Avoid exposing database connection details or secrets.
        return {
            "success": False,
            "error": "Knowledge search is temporarily unavailable.",
            "results": []
        }


@tool
def business_hours() -> dict:
    """
    Return the company's business hours.
    """

    return {
        "success": True,
        "business_hours": {
            "Monday": "9:00 AM - 5:00 PM",
            "Tuesday": "9:00 AM - 5:00 PM",
            "Wednesday": "9:00 AM - 5:00 PM",
            "Thursday": "9:00 AM - 5:00 PM",
            "Friday": "9:00 AM - 5:00 PM",
            "Saturday": "Closed",
            "Sunday": "Closed"
        }
    }