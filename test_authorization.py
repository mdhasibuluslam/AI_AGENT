from authorization import (
    get_user_roles,
    get_user_permissions,
    has_permission,
)

TEST_USER_ID = 1 # তোমার actual test user ID বসাও


def test_customer_permissions():
    roles = get_user_roles(TEST_USER_ID)
    permissions = get_user_permissions(TEST_USER_ID)

    print("Roles:", roles)
    print("Permissions:", permissions)

    assert "customer" in roles
    assert "chat:use" in permissions
    assert has_permission(TEST_USER_ID, "chat:use")
    assert not has_permission(TEST_USER_ID, "users:manage")

    print("PASS: customer authorization")


if __name__ == "__main__":
    test_customer_permissions()