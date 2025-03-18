# tests/unit/test_get_differences.py
import unittest
from src.lambda_code.main import get_differences

class TestGetDifferences(unittest.TestCase):
    def test_empty_lists(self):
        """Test behavior when both lists are empty"""
        result = get_differences(iter([]), iter([]))
        self.assertEqual(result["create"], [])
        self.assertEqual(result["disable"], [])
        self.assertEqual(result["enable"], [])

    def test_new_users(self):
        """Test when there are new users in IdC that don't exist in WorkMail"""
        idc_users = iter(["user1", "user2"])
        workmail_users = iter([])
        result = get_differences(idc_users, workmail_users)
        self.assertEqual(result["create"], ["user1", "user2"])
        self.assertEqual(result["disable"], [])
        self.assertEqual(result["enable"], [])

    def test_users_to_disable(self):
        """Test when there are users in WorkMail that don't exist in IdC"""
        idc_users = iter([])
        workmail_users = iter([{
            "IdentityProviderUserId": "user1",
            "State": "ENABLED"
        }])
        result = get_differences(idc_users, workmail_users)
        self.assertEqual(result["create"], [])
        self.assertEqual(len(result["disable"]), 1)
        self.assertEqual(result["disable"][0]["IdentityProviderUserId"], "user1")
        self.assertEqual(result["enable"], [])

    def test_users_to_enable(self):
        """Test when there are disabled users in WorkMail that exist in IdC"""
        idc_users = iter(["user1"])
        workmail_users = iter([{
            "IdentityProviderUserId": "user1",
            "State": "DISABLED"
        }])
        result = get_differences(idc_users, workmail_users)
        self.assertEqual(result["create"], [])
        self.assertEqual(result["disable"], [])
        self.assertEqual(len(result["enable"]), 1)
        self.assertEqual(result["enable"][0]["IdentityProviderUserId"], "user1")

    def test_users_to_enable_with_deleted(self):
        """Test when there are disabled users in WorkMail that exist in IdC"""
        idc_users = iter(["user1"])
        workmail_users = iter([{
            "IdentityProviderUserId": "user1",
            "State": "DISABLED",
            },
            {
                "IdentityProviderUserId": "user2",
                "State": "DELETED"
            }])
        result = get_differences(idc_users, workmail_users)
        self.assertEqual(result["create"], [])
        self.assertEqual(result["disable"], [])
        self.assertEqual(len(result["enable"]), 1)
        self.assertEqual(result["enable"][0]["IdentityProviderUserId"], "user1")

    def test_users_to_enable_idc_and_workmail_different(self):
        """Test when there is new user in IdC which should be created in WorkMail, and old user in WorkMail which
        should be disabled"""
        idc_users = iter(["user1"])
        workmail_users = iter([{
            "IdentityProviderUserId": "user2",
            "State": "ENABLED"
        }])
        result = get_differences(idc_users, workmail_users)
        self.assertEqual(result["create"], ["user1"])
        self.assertEqual(len(result["disable"]), 1)
        self.assertEqual(result["disable"][0]["IdentityProviderUserId"], "user2")
        self.assertEqual(result["enable"], [])
