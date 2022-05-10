import kdb
import unittest

from ..main import dns_plugin

VALID_DOMAIN = "libelektra.org"
INVALID_DOMAIN = "www.does-not.exist"


class Key(unittest.TestCase):

    def setUp(self):
        self.parent_key = kdb.Key("user:/python")
        self.plugin = dns_plugin.ElektraPlugin()
        self.valid_key_with_plugin = kdb.Key("user:/python/hostname",
                                             kdb.KEY_VALUE, VALID_DOMAIN,
                                             kdb.KEY_META, "check/dns", ""
                                             )
        self.invalid_key_with_plugin = kdb.Key("user:/python/hostname",
                                               kdb.KEY_VALUE, INVALID_DOMAIN,
                                               kdb.KEY_META, "check/dns", ""
                                               )
        self.valid_key_without_plugin = kdb.Key("user:/foo/bar",
                                                kdb.KEY_VALUE, "val"
                                                )

        self.invalid_ks = kdb.KeySet(10, self.invalid_key_with_plugin, self.valid_key_without_plugin, kdb.KS_END)
        self.valid_ks = kdb.KeySet(10, self.valid_key_with_plugin, self.valid_key_without_plugin, kdb.KS_END)

    def test_get_ipv4_from_hostname_exists(self):
        self.assertTrue(dns_plugin.get_ipv4_by_hostname(hostname=VALID_DOMAIN))

    def test_get_ipv4_from_hostname_does_not_exist(self):
        with self.assertRaises(Exception):
            dns_plugin.get_ipv4_by_hostname(hostname=INVALID_DOMAIN)

    def test_check_valid_key_meta_is_set_returns_true(self):
        self.assertTrue(dns_plugin.check_key(self.valid_key_with_plugin))

    def test_check_invalid_key_meta_is_set_returns_false(self):
        self.assertFalse(dns_plugin.check_key(self.invalid_key_with_plugin))

    def test_check_key_meta_is_not_set_returns_false(self):
        self.assertTrue(dns_plugin.check_key(self.valid_key_without_plugin))

    def test_set_containing_invalid_key_returns_failure(self):
        self.assertEqual(-1, self.plugin.set(self.invalid_ks, self.parent_key))

    def test_set_containing_valid_key_returns_success(self):
        self.assertEqual(1, self.plugin.set(self.valid_ks, self.parent_key))


if __name__ == '__main__':
    unittest.main()
