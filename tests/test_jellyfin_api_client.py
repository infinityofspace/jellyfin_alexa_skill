import unittest
from collections import OrderedDict

import requests

from jellyfin_alexa_skill.jellyfin.api.client import JellyfinClient, MediaType

AUDIO_MEDIA_IDS = [
    # "song title" by "artist"
    "ccf19d58cf1a38fa18ea0e2dd0da0e5b",
    # "song title 2" by "artist 2"
    "52d1ba6abce1e968d3be5da9fcce4acf"
]

VIDEO_MEDIA_IDS = [
    # "video name"
    "c741c509a31b9192e0590d6ca6e66e3e"
]

ARTISTS_IDS = [
    # "artist"
    "6ed4179f2c585635bdc89494c581d846",
    # "artist 2"
    "256ec0d6eb43e6590520f2122248dd4c"
]

PLAYLISTS = OrderedDict([
    # "Playlist Audio 1"
    (
        "bf7657eb4096f9894799d6476e316563", [
            "ccf19d58cf1a38fa18ea0e2dd0da0e5b",
            "52d1ba6abce1e968d3be5da9fcce4acf"
        ]
    ),
    # "Playlist Audio 2"
    (
        "272a9efb388ff4f05868880dd051b75b", [
            "ccf19d58cf1a38fa18ea0e2dd0da0e5b"
        ]
    ),
    # "Playlist Empty"
    (
        "6db7221fa8491264c14c8af55c56ce79", []
    ),
    # "Playlist Mixed"
    (
        "92857a45e40f78084b10c017a60f3560", [
            "c741c509a31b9192e0590d6ca6e66e3e",
            "ccf19d58cf1a38fa18ea0e2dd0da0e5b"
        ]
    )
])

RECENTLY_ADDED_MEDIA_IDS = [
    "c741c509a31b9192e0590d6ca6e66e3e",
]

USERNAME = "jellyfin-alexa-skill"
PASSWORD = "pw"


class TestJellyfinApiClient(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = JellyfinClient(server_endpoint="http://localhost:8096")
        cls.user_id, cls.token = cls.client.get_auth_token(USERNAME, PASSWORD)

    def test_connection(self):
        """
        Test if the connection to the server is working.
        """

        info = self.client.public_info()

        self.assertIsNotNone(info)

    def test_valid_authentication(self):
        """
        Test if a user id and token is returned.
        """

        user_id, token = self.client.get_auth_token(USERNAME, PASSWORD)

        self.assertIsNotNone(user_id)
        self.assertIsNotNone(token)

    def test_invalid_authentication(self):
        """
        Test if the authentication fails with an invalid username and password.
        """

        try:
            self.client.get_auth_token(USERNAME, "pass")
            self.assertTrue(False)
        except requests.exceptions.HTTPError as e:
            self.assertEqual(e.response.status_code, 401)

        try:
            self.client.get_auth_token("abc", PASSWORD)
            self.assertTrue(False)
        except requests.exceptions.HTTPError as e:
            self.assertEqual(e.response.status_code, 401)

    def test_public_info(self):
        """
        Test if the public info is returned.
        """

        info = self.client.public_info()

        # clear server name, because the name is not the same on every start
        info["ServerName"] = None
        # clear server address, because the address is not the same on each system and depends on docker
        info["LocalAddress"] = None

        valid_info = {
            "LocalAddress": None,
            "ServerName": None,
            "Version": "10.7.7",
            "ProductName": "Jellyfin Server",
            "OperatingSystem": "Linux",
            "Id": "e7f6bf36577c4a42b12943e27ec8fba6",
            "StartupWizardCompleted": True
        }

        self.assertEqual(info, valid_info)

    def test_public_info_server_not_reachable(self):
        """
        Test if the connection to the server throws an exception.
        """

        # change the server endpoint to an unreachable one
        client = JellyfinClient(server_endpoint="http://localhost:1")

        try:
            client.public_info()
            self.assertTrue(False)
        except requests.exceptions.ConnectionError as e:
            self.assertTrue(True)

    def test_get_stream_url(self):
        # TODO: implement
        pass

    def test_get_ancestor_with_image(self):
        # TODO: implement
        pass

    def test_get_art_url(self):
        # TODO: implement
        pass

    def test_get_favorites(self):
        """
        Test if all favorites are returned.
        """

        # cleanup all favorites
        for i in AUDIO_MEDIA_IDS + VIDEO_MEDIA_IDS:
            self.client.unfavorite(user_id=self.user_id, token=self.token, media_id=i)

        with self.subTest("no favorites"):
            favorites = self.client.get_favorites(user_id=self.user_id, token=self.token)
            self.assertEqual(len(favorites), 0)

        # add one favorite
        self.client.favorite(user_id=self.user_id, token=self.token, media_id=AUDIO_MEDIA_IDS[0])

        with self.subTest("no favorites"):
            favorites = self.client.get_favorites(user_id=self.user_id, token=self.token)
            self.assertEqual(len(favorites), 1)
            self.assertEqual(favorites[0]["Id"], AUDIO_MEDIA_IDS[0])

        # add one more favorite
        self.client.favorite(user_id=self.user_id, token=self.token, media_id=AUDIO_MEDIA_IDS[1])

        with self.subTest("no favorites"):
            favorites = self.client.get_favorites(user_id=self.user_id, token=self.token)
            self.assertEqual(len(favorites), 2)
            ids = [f["Id"] for f in favorites]
            self.assertIn(AUDIO_MEDIA_IDS[0], ids)
            self.assertIn(AUDIO_MEDIA_IDS[1], ids)

    def test_get_playlist(self):
        """
        Test if playlists by their name are returned.
        """

        with self.subTest("search for playlist which name contains 'Playlist Audio 1'"):
            playlist_results = self.client.get_playlist(user_id=self.user_id, token=self.token,
                                                        playlist_name="Playlist Audio 1")
            self.assertEqual(len(playlist_results), 1)
            self.assertEqual(playlist_results[0]["Id"], list(PLAYLISTS.keys())[0])

        with self.subTest("search for playlist which name contains 'Playlist Audio'"):
            playlist_results = self.client.get_playlist(user_id=self.user_id, token=self.token,
                                                        playlist_name="Playlist Audio")
            # it should return both playlists "Playlist Audio 1" and "Playlist Audio 2"
            self.assertEqual(len(playlist_results), 2)

        with self.subTest("search for playlist with an empty search term"):
            playlist_results = self.client.get_playlist(user_id=self.user_id, token=self.token,
                                                        playlist_name="")
            # it should return both playlists "Playlist Audio 1" and "Playlist Audio 2"
            self.assertEqual(len(playlist_results), len(PLAYLISTS.keys()))
            ids = [playlist["Id"] for playlist in playlist_results]
            for i in PLAYLISTS.keys():
                self.assertIn(i, ids)

        with self.subTest("search for playlist with an None search term"):
            playlist_results = self.client.get_playlist(user_id=self.user_id, token=self.token,
                                                        playlist_name=None)
            # it should return both playlists "Playlist Audio 1" and "Playlist Audio 2"
            self.assertEqual(len(playlist_results), len(PLAYLISTS.keys()))
            ids = [playlist["Id"] for playlist in playlist_results]
            for i in PLAYLISTS.keys():
                self.assertIn(i, ids)

    def test_get_playlist_items(self):
        """
        Test if all items of a specific playlist are returned
        """

        with self.subTest("get all items of playlist 'Playlist Audio 1'"):
            playlist_id = list(PLAYLISTS.keys())[0]
            playlist_items = self.client.get_playlist_items(user_id=self.user_id, token=self.token,
                                                            playlist_id=playlist_id)
            self.assertEqual(len(playlist_items), len(PLAYLISTS[playlist_id]))
            ids = [item["Id"] for item in playlist_items]
            for i in PLAYLISTS[playlist_id]:
                self.assertIn(i, ids)

        with self.subTest("get all items of playlist 'Playlist Empty'"):
            playlist_id = list(PLAYLISTS.keys())[2]
            playlist_items = self.client.get_playlist_items(user_id=self.user_id, token=self.token,
                                                            playlist_id=playlist_id)
            self.assertEqual(len(playlist_items), 0)

        with self.subTest("get all items of playlist 'Playlist Mixed'"):
            playlist_id = list(PLAYLISTS.keys())[2]
            playlist_items = self.client.get_playlist_items(user_id=self.user_id, token=self.token,
                                                            playlist_id=playlist_id)
            self.assertEqual(len(playlist_items), len(PLAYLISTS[playlist_id]))
            ids = [item["Id"] for item in playlist_items]
            for i in PLAYLISTS[playlist_id]:
                self.assertIn(i, ids)

    def test_search_media_items(self):
        """
        Test if media items are returned by their name.
        """

        with self.subTest("search for media item which name contains 'song title"):
            search_results = self.client.search_media_items(user_id=self.user_id,
                                                            token=self.token,
                                                            term="song title",
                                                            media=MediaType.AUDIO)
            self.assertEqual(len(search_results), 2)
            ids = [search_result["Id"] for search_result in search_results]
            self.assertIn(AUDIO_MEDIA_IDS[0], ids)
            self.assertIn(AUDIO_MEDIA_IDS[1], ids)

        with self.subTest("search for media item which name contains 'song title 2"):
            search_results = self.client.search_media_items(user_id=self.user_id,
                                                            token=self.token,
                                                            term="song title 2",
                                                            media=MediaType.AUDIO)
            self.assertEqual(len(search_results), 1)
            self.assertEqual(search_results[0]["Id"], AUDIO_MEDIA_IDS[1])

        with self.subTest("search for media item with empty search term"):
            search_results = self.client.search_media_items(user_id=self.user_id,
                                                            token=self.token,
                                                            term="",
                                                            media=MediaType.AUDIO)
            self.assertEqual(len(search_results), len(AUDIO_MEDIA_IDS))
            ids = [search_result["Id"] for search_result in search_results]
            for i in AUDIO_MEDIA_IDS:
                self.assertIn(i, ids)

        with self.subTest("search for media item with None search term"):
            search_results = self.client.search_media_items(user_id=self.user_id,
                                                            token=self.token,
                                                            term=None,
                                                            media=MediaType.AUDIO)
            self.assertEqual(len(search_results), len(AUDIO_MEDIA_IDS))
            ids = [search_result["Id"] for search_result in search_results]
            for i in AUDIO_MEDIA_IDS:
                self.assertIn(i, ids)

    def test_get_artist_items(self):
        """
        Test if items of a specific artist are returned.
        """

        with self.subTest("get artist items of artist with name 'artist 2'"):
            artist_items = self.client.get_artist_items(user_id=self.user_id,
                                                        token=self.token,
                                                        artist_id=ARTISTS_IDS[1],
                                                        media=MediaType.AUDIO)
            self.assertEqual(len(artist_items), 1)
            self.assertEqual(artist_items[0]["Id"], AUDIO_MEDIA_IDS[1])

        with self.subTest("get artist items of artist which does not exist"):
            artist_items = self.client.get_artist_items(user_id=self.user_id,
                                                        token=self.token,
                                                        artist_id="42",
                                                        media=MediaType.AUDIO)
            # it should return all items (Playlists, Songs, etc.)
            self.assertEqual(len(artist_items), 5)

    def test_search_artists(self):
        """
        Test search for artists with a search term.
        """

        with self.subTest("search artists with name contains 'artist 2'"):
            search_results = self.client.search_artist(user_id=self.user_id, token=self.token, term="artist 2")
            self.assertEqual(len(search_results), 1)
            self.assertEqual(search_results[0]["Id"], ARTISTS_IDS[1])

        with self.subTest("search artists with name contains 'artist"):
            search_results = self.client.search_artist(user_id=self.user_id, token=self.token, term="artist")
            # it should return artist with name 'artist' and 'artist 2'
            self.assertEqual(len(search_results), 2)
            ids = [res["Id"] for res in search_results]
            for i in ARTISTS_IDS:
                self.assertIn(i, ids)

        with self.subTest("search artists by empty search term"):
            search_results = self.client.search_artist(user_id=self.user_id, token=self.token, term="")
            # it should return all artists
            self.assertEqual(len(search_results), 2)
            ids = [res["Id"] for res in search_results]
            for i in ARTISTS_IDS:
                self.assertIn(i, ids)

        with self.subTest("search artists by None search term"):
            search_results = self.client.search_artist(user_id=self.user_id, token=self.token, term=None)
            # it should return all artists
            self.assertEqual(len(search_results), 2)
            ids = [res["Id"] for res in search_results]
            for i in ARTISTS_IDS:
                self.assertIn(i, ids)

    def test_get_recently_added_items(self):
        """
        Test if recently added items are returned.
        """

        recently_added_media = self.client.get_recently_added(user_id=self.user_id, token=self.token)
        self.assertEqual(len(recently_added_media), len(RECENTLY_ADDED_MEDIA_IDS))
        ids = [media["Id"] for media in recently_added_media]
        for i in RECENTLY_ADDED_MEDIA_IDS:
            self.assertIn(i, ids)

    def test_favorite_item(self):
        """
        Test if an item is added to the favorites.
        """

        media_id = AUDIO_MEDIA_IDS[0]

        # first unfavorite the item, to make sure it is not already favorited
        result = self.client.unfavorite(user_id=self.user_id, token=self.token, media_id=media_id)
        self.assertFalse(result["IsFavorite"])

        result = self.client.favorite(user_id=self.user_id, token=self.token, media_id=media_id)
        self.assertTrue(result["IsFavorite"])

    def test_unfavorite_item(self):
        """
        Test if an item is removed from the favorites.
        """

        media_id = AUDIO_MEDIA_IDS[0]

        # first favorite the item, to make sure it is favorited
        result = self.client.favorite(user_id=self.user_id, token=self.token, media_id=media_id)
        self.assertTrue(result["IsFavorite"])

        result = self.client.unfavorite(user_id=self.user_id, token=self.token, media_id=media_id)
        self.assertFalse(result["IsFavorite"])


if __name__ == "__main__":
    unittest.main()
