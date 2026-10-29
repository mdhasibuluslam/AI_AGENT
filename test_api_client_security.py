
from unittest.mock import Mock, patch

import requests

from api_client import search_products


def test_rejects_empty_query_without_http_request():
    with patch("api_client.requests.get") as mock_get:
        result = search_products("   ")

    assert result["success"] is False
    mock_get.assert_not_called()


def test_rejects_oversized_query_without_http_request():
    with patch("api_client.requests.get") as mock_get:
        result = search_products("a" * 201)

    assert result["success"] is False
    mock_get.assert_not_called()


@patch("api_client.requests.get")
def test_valid_response(mock_get):
    response = Mock()
    response.json.return_value = {"products": [{"id": 1}]}
    response.raise_for_status.return_value = None
    mock_get.return_value = response

    result = search_products("laptop")

    assert result["success"] is True
    assert result["data"]["products"][0]["id"] == 1
    mock_get.assert_called_once_with(
        "https://dummyjson.com/products/search",
        params={"q": "laptop"},
        timeout=10,
    )


@patch("api_client.requests.get")
def test_timeout_returns_safe_error(mock_get):
    mock_get.side_effect = requests.Timeout("internal timeout details")

    result = search_products("laptop")

    assert result["success"] is False
    assert result["error"] == "Product API timed out."
    assert "internal timeout details" not in result["error"]


@patch("api_client.requests.get")
def test_request_exception_does_not_leak_details(mock_get):
    mock_get.side_effect = requests.ConnectionError(
        "sensitive internal connection details"
    )

    result = search_products("laptop")

    assert result["success"] is False
    assert result["error"] == "Product API request failed."
    assert "sensitive internal" not in result["error"]


@patch("api_client.requests.get")
def test_rejects_invalid_json(mock_get):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.side_effect = ValueError("invalid JSON")
    mock_get.return_value = response

    result = search_products("laptop")

    assert result["success"] is False
    assert "invalid response" in result["error"]


@patch("api_client.requests.get")
def test_rejects_unexpected_product_structure(mock_get):
    response = Mock()
    response.raise_for_status.return_value = None
    response.json.return_value = {"products": "not-a-list"}
    mock_get.return_value = response

    result = search_products("laptop")

    assert result["success"] is False
    assert "product list" in result["error"]
