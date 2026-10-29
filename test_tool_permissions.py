
from unittest.mock import patch

import pytest

from authorization import has_permission


def test_customer_can_use_chat():
    with patch(
        "authorization.get_user_permissions",
        return_value={"chat:use"},
    ):
        assert has_permission(1, "chat:use") is True


def test_customer_cannot_manage_support():
    with patch(
        "authorization.get_user_permissions",
        return_value={"chat:use"},
    ):
        assert has_permission(1, "support:manage") is False


def test_customer_cannot_manage_users():
    with patch(
        "authorization.get_user_permissions",
        return_value={"chat:use"},
    ):
        assert has_permission(1, "users:manage") is False


def test_support_agent_can_manage_support():
    with patch(
        "authorization.get_user_permissions",
        return_value={"chat:use", "support:manage"},
    ):
        assert has_permission(2, "support:manage") is True


def test_admin_can_manage_users():
    with patch(
        "authorization.get_user_permissions",
        return_value={"chat:use", "support:manage", "users:manage"},
    ):
        assert has_permission(3, "users:manage") is True
