
from unittest.mock import patch

from tools import product_search


def test_empty_product_name_is_rejected():
    with patch("tools.search_products") as mock_search:
        result = product_search.invoke({"product_name": "   "})

    assert result["success"] is False
    assert "empty" in result["error"].lower()
    mock_search.assert_not_called()


def test_oversized_product_name_is_rejected():
    with patch("tools.search_products") as mock_search:
        result = product_search.invoke({
            "product_name": "a" * 201
        })

    assert result["success"] is False
    assert "200 characters" in result["error"]
    mock_search.assert_not_called()


def test_valid_product_name_is_trimmed():
    with patch(
        "tools.search_products",
        return_value={
            "success": True,
            "data": {
                "products": [{
                    "id": 1,
                    "title": "Test Laptop",
                    "price": 1000,
                    "stock": 10,
                    "rating": 4.5
                }]
            }
        }
    ) as mock_search:
        result = product_search.invoke({
            "product_name": "  Laptop  "
        })

    mock_search.assert_called_once_with("Laptop")
    assert result["success"] is True
    assert result["product"]["name"] == "Test Laptop"
