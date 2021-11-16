import unittest

import requests

from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class TestJellyfinApiClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = JellyfinClient(server_endpoint="http://localhost:8096")

    def test_connection(self):
        info = self.client.public_info()

        self.assertIsNotNone(info)

    def test_valid_authentication(self):
        user_id, token = self.client.get_auth_token("jellyfin-alexa-skill", "pw")

        self.assertIsNotNone(user_id)
        self.assertIsNotNone(token)

    def test_invalid_authentication(self):
        try:
            self.client.get_auth_token("jellyfin-alexa-skill", "pass")
            self.assertTrue(False)
        except requests.exceptions.HTTPError as e:
            self.assertEqual(e.response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
