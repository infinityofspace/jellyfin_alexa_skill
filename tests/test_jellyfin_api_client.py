import unittest

from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient


class TestJellyfinApiClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = JellyfinClient(server_endpoint="http://localhost:8096")

    def test_connection(self):
        info = self.client.public_info()

        self.assertIsNotNone(info)


if __name__ == "__main__":
    unittest.main()
