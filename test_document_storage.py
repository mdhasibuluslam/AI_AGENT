
from unittest.mock import patch

import pytest

from document_storage import save_document_chunks


def test_invalid_user_id_is_rejected():
    with pytest.raises(ValueError):
        save_document_chunks(0, 10, ["hello"])


def test_invalid_file_id_is_rejected():
    with pytest.raises(ValueError):
        save_document_chunks(7, -1, ["hello"])


def test_empty_chunks_are_rejected():
    with pytest.raises(ValueError):
        save_document_chunks(7, 10, [])


def test_empty_chunk_is_rejected():
    with pytest.raises(ValueError):
        save_document_chunks(7, 10, ["hello", " "])


def test_non_string_chunk_is_rejected():
    with pytest.raises(ValueError):
        save_document_chunks(7, 10, ["hello", None])


def test_user_cannot_store_chunks_in_another_users_file():
    with patch("document_storage.get_connection") as mock_connection:
        conn = mock_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = None

        with pytest.raises(PermissionError):
            save_document_chunks(7, 10, ["private text"])

        sql, params = cursor.execute.call_args.args

        assert "WHERE id = %s AND user_id = %s" in sql
        assert params == (10, 7)
        cursor.executemany.assert_not_called()


def test_valid_chunks_are_inserted_for_file_owner():
    with patch("document_storage.get_connection") as mock_connection:
        conn = mock_connection.return_value.__enter__.return_value
        cursor = conn.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = (10,)

        result = save_document_chunks(
            7,
            10,
            ["first chunk", "second chunk"],
        )

        assert result == 2
        insert_call = [
            call for call in cursor.execute.call_args_list
            if "DELETE FROM document_chunks" in call.args[0]
        ]
        assert len(insert_call) == 1

        cursor.executemany.assert_called_once()
        sql, rows = cursor.executemany.call_args.args
        assert "INSERT INTO document_chunks" in sql
        assert rows == [
            (7, 10, 0, "first chunk"),
            (7, 10, 1, "second chunk"),
        ]
