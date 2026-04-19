import os
import sys
import unittest
from types import ModuleType, SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if "requests" not in sys.modules:
    requests_stub = ModuleType("requests")
    requests_stub.get = lambda *args, **kwargs: None
    requests_stub.post = lambda *args, **kwargs: None
    requests_stub.exceptions = SimpleNamespace(RequestException=Exception)
    sys.modules["requests"] = requests_stub


class TestLiveClobCreds(unittest.TestCase):
    def test_init_real_client_blocks_eager_derivation_by_default(self):
        import core.exchange as exchange_mod
        from core.exchange import PolymarketExchange

        class DummyClobClient:
            def __init__(self, *args, **kwargs):
                pass

            def create_or_derive_api_creds(self):
                raise AssertionError("should not derive creds in this test")

        class DummyApiCreds:
            def __init__(self, api_key, api_secret, api_passphrase):
                self.api_key = api_key
                self.api_secret = api_secret
                self.api_passphrase = api_passphrase

        py_clob_client = ModuleType("py_clob_client")
        client_mod = ModuleType("py_clob_client.client")
        clob_types_mod = ModuleType("py_clob_client.clob_types")
        client_mod.ClobClient = DummyClobClient
        clob_types_mod.ApiCreds = DummyApiCreds

        original_client_pkg = sys.modules.get("py_clob_client")
        original_client_mod = sys.modules.get("py_clob_client.client")
        original_clob_types_mod = sys.modules.get("py_clob_client.clob_types")
        sys.modules["py_clob_client"] = py_clob_client
        sys.modules["py_clob_client.client"] = client_mod
        sys.modules["py_clob_client.clob_types"] = clob_types_mod

        settings = exchange_mod.SETTINGS
        original = (
            settings.private_key,
            settings.funder_address,
            settings.clob_api_key,
            settings.clob_api_secret,
            settings.clob_api_passphrase,
            getattr(settings, "allow_clob_cred_derivation", False),
        )
        try:
            settings.private_key = "pk"
            settings.funder_address = "0xfunder"
            settings.clob_api_key = ""
            settings.clob_api_secret = ""
            settings.clob_api_passphrase = ""
            settings.allow_clob_cred_derivation = False

            with self.assertRaisesRegex(
                ValueError, "CLOB_API_\\* credentials are required"
            ):
                PolymarketExchange(dry_run=False)
        finally:
            (
                settings.private_key,
                settings.funder_address,
                settings.clob_api_key,
                settings.clob_api_secret,
                settings.clob_api_passphrase,
                settings.allow_clob_cred_derivation,
            ) = original
            if original_client_pkg is None:
                sys.modules.pop("py_clob_client", None)
            else:
                sys.modules["py_clob_client"] = original_client_pkg
            if original_client_mod is None:
                sys.modules.pop("py_clob_client.client", None)
            else:
                sys.modules["py_clob_client.client"] = original_client_mod
            if original_clob_types_mod is None:
                sys.modules.pop("py_clob_client.clob_types", None)
            else:
                sys.modules["py_clob_client.clob_types"] = original_clob_types_mod


if __name__ == "__main__":
    unittest.main()
