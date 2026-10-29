
from unittest.mock import patch

from file_service import save_uploaded_file, list_user_files


def test_save_uploaded_file_returns_metadata():
    fake_row = (
        10,
        "policy.txt",
        ".txt",
        52,
        "2026-10-29T10:00:00+00:00",
    )

    with patch("file_service.get_connection") as mock_connection:
        conn = mock_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = fake_row

        result = save_uploaded_file(
            7,
            {
                "filename": "policy.txt",
                "content_type": ".txt",
                "characters": 52,
                "text": "Customers can return eligible products within 30 days.",
            },
        )

    assert result["id"] == 10
    assert result["filename"] == "policy.txt"
    assert "text" not in result


def test_list_user_files_returns_metadata_only():
    fake_row = (10, "policy.txt", ".txt", 52, "2026-10-29T10:00:00+00:00")

    with patch("file_service.get_connection") as mock_connection:
        conn = mock_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [fake_row]

        result = list_user_files(7)

    assert len(result) == 1
    assert result[0]["id"] == 10
    assert "text" not in result[0]


def test_save_rejects_invalid_user_id():
    import pytest

    with pytest.raises(ValueError):
        save_uploaded_file(
            0,
            {
                "filename": "policy.txt",
                "content_type": ".txt",
                "characters": 1,
                "text": "x",
            },
        )

from unittest.mock import patch

from file_service import list_user_files, save_uploaded_file


def test_list_files_uses_authenticated_user_id():
    with patch("file_service.get_connection") as mock_connection:
        conn = mock_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = []

        result = list_user_files(7)

        assert result == []
        cursor.execute.assert_called_once()

        sql, params = cursor.execute.call_args.args
        assert "WHERE user_id = %s" in sql
        assert params == (7,)


def test_upload_is_saved_under_authenticated_user_id():
    fake_row = (
        10,
        "policy.txt",
        ".txt",
        5,
        "2026-10-29T10:00:00+00:00",
    )

    with patch("file_service.get_connection") as mock_connection:
        conn = mock_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = fake_row

        save_uploaded_file(
            7,
            {
                "filename": "policy.txt",
                "content_type": ".txt",
                "characters": 5,
                "text": "Hello",
            },
        )

        sql, params = cursor.execute.call_args.args
        assert "INSERT INTO uploaded_files" in sql
        assert params[0] == 7