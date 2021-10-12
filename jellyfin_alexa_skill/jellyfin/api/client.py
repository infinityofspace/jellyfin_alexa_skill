import urllib.parse
from enum import Enum
from typing import Optional

from jellyfin_apiclient_python import JellyfinClient as Client
from jellyfin_apiclient_python.exceptions import HTTPException

from jellyfin_alexa_skill import __version__
from jellyfin_alexa_skill.config import APP_NAME


class MediaType(Enum):
    AUDIO = "Audio"
    VIDEO = "Video"


class JellyfinClient(Client):

    def __init__(self,
                 server_url: str,
                 username: str,
                 password: str,
                 device_id: str,
                 device_name: str):
        super(JellyfinClient, self).__init__()
        self.config.app(name=APP_NAME, version=__version__, device_name=device_name, device_id=device_id)
        self.config.data["auth.ssl"] = True

        self.auth.connect_to_address(address=server_url)
        self.auth.login(server_url=server_url, username=username, password=password)
        cred = self.get_credentials()
        self.authenticate(cred)

        # def event(event_name, data):
        #     print(event_name, data)
        #     # if event_name == "WebSocketDisconnect":
        #     #     timeout_gen = expo(100)
        #     #     if server["uuid"] in self.clients:
        #     #         while not self.is_stopping:
        #     #             timeout = next(timeout_gen)
        #     #             logging.info(
        #     #                 "No connection to server. Next try in {0} second(s)".format(
        #     #                     timeout
        #     #                 )
        #     #             )
        #     #             self._disconnect_client(server=server)
        #     #             time.sleep(timeout)
        #     #             if self.connect_client(server):
        #     #                 break
        #     # else:
        #     #     self.callback(client, event_name, data)
        #
        # self.callback = event
        # self.callback_ws = event
        # self.start(websocket=True)
        #
        # self.jellyfin.post_capabilities(CAPABILITIES_AUDIO)

    def get_stream_url(self,
                       item_id: str,
                       audio_codec: str = "mp3",
                       max_streaming_bitrate: int = 140000000,
                       **kwargs) -> str:
        """
        Generate a url which allows streaming the requested media file.
        """

        play_info = self.jellyfin.get_play_info(item_id, profile=None)

        url = self.config.data["auth.server"]
        path = f"Audio/{item_id}/universal"
        params = {
            'UserId': self.http.config.data["auth.user_id"],
            'DeviceId': self.http.config.data["app.device_id"],
            "MaxStreamingBitrate": max_streaming_bitrate,
            "PlaySessionId": play_info["PlaySessionId"],
            "api_key": self.config.data["auth.token"],
            "AudioCodec": audio_codec
        }
        params.update(kwargs)

        params_url = urllib.parse.urlencode(params)

        url = urllib.parse.urljoin(url, path)
        url += "?" + params_url

        return url

    def get_favorites(self, media_type: Optional[MediaType] = None, **kwargs):
        params = {
            "Filters": "IsFavorite",
            "Recursive": True
        }
        params.update(kwargs)

        if media_type:
            params["IncludeItemTypes"] = media_type.value

        return self.jellyfin.user_items(params=params)["Items"]

    def get_playlist(self, playlist_name: Optional[str] = None, **kwargs):
        params = {
            "IncludeItemTypes": "Playlist",
            "Recursive": True
        }
        params.update(kwargs)

        if playlist_name:
            params["searchTerm"] = playlist_name

        return self.jellyfin.user_items(params=params)["Items"]

    def get_playlist_items(self, playlist_id: str, **kwargs):
        params = {
            "UserId": "{UserId}"
        }
        params.update(kwargs)

        try:
            return self.jellyfin._get(f"Playlists/{playlist_id}/Items", params=params)["Items"]
        except HTTPException as e:
            if e.status == 400:
                # the playlist does not exist
                return None

            raise e

    def search_media_items(self, term: str, media: MediaType, limit=20, **kwargs):
        params = {
            "searchTerm": term,
            "Recursive": True,
            "IncludeItemTypes": media.value,
            "Limit": limit
        }
        params.update(kwargs)

        return self.jellyfin.user_items(params=params)["Items"]

    def get_artist_items(self, author_id: str, media: MediaType, **kwargs):
        params = {
            "ArtistIds": author_id,
            "Recursive": True,
            "MediaTypes": media.value,
        }
        params.update(kwargs)

        return self.jellyfin.user_items(params=params)["Items"]

    def search_artist(self, term, **kwargs):
        params = {
            "UserId": "{UserId}",
            "searchTerm": term,
            "Recursive": True
        }
        params.update(kwargs)

        return self.jellyfin._get("Artists", params=params)["Items"]
