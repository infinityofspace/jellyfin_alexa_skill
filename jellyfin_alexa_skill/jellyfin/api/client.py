import json
import urllib.parse
import urllib.parse
from enum import Enum
from typing import Optional, Tuple

import requests

from jellyfin_alexa_skill import __version__
from jellyfin_alexa_skill.config import APP_NAME


class MediaType(Enum):
    AUDIO = "Audio"
    VIDEO = "Video"


class JellyfinClient:

    def __init__(self, server_endpoint: str, client_name=APP_NAME):
        self.server_endpoint = server_endpoint
        self.client_name = client_name

    @staticmethod
    def _build_emby_auth_header(client_name=APP_NAME,
                                device_name="NONE",
                                device_id="NONE",
                                version=__version__,
                                token=None):
        header = f"MediaBrowser Client={client_name}, Device={device_name}, DeviceId={device_id}, Version={version}"

        if token:
            header += ", Token={}".format(token)

        return header

    def public_info(self) -> Optional[dict]:
        url = self.server_endpoint + "/System/Info/Public"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header()
        }

        res = requests.get(url, headers=headers)

        if res:
            return json.loads(res.content)
        else:
            return None

    def get_auth_token(self,
                       username: str,
                       password: str) -> Tuple[str, str]:
        data = {
            "Username": username,
            "Pw": password
        }

        url = self.server_endpoint + "/Users/authenticatebyname"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header()
        }

        res = requests.post(url, headers=headers, data=json.dumps(data))

        if res:
            json_res = json.loads(res.content)
            return json_res["User"]["Id"], json_res["AccessToken"]
        else:
            res.raise_for_status()

    def get_stream_url(self,
                       user_id: str,
                       token: str,
                       item_id: str,
                       device_id: str = "NONE",
                       audio_codec: str = "mp3",
                       max_streaming_bitrate: int = 140000000,
                       start_time_ticks: int = 0,
                       **kwargs) -> str:
        """
        Generate a url which allows streaming the requested media file.
        """

        data = {
            "UserId": user_id,
            "StartTimeTicks": start_time_ticks,
            "AutoOpenLiveStream": True,
            "IsPlayback": True
        }

        url = self.server_endpoint + f"/Items/{item_id}/PlaybackInfo"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.post(url, headers=headers, data=json.dumps(data))
        if res:
            play_info = json.loads(res.content)
        else:
            res.raise_for_status()

        url = self.server_endpoint
        path = f"/Audio/{item_id}/universal"
        params = {
            'UserId': user_id,
            'DeviceId': device_id,
            "MaxStreamingBitrate": max_streaming_bitrate,
            "PlaySessionId": play_info["PlaySessionId"],
            "api_key": token,
            "AudioCodec": audio_codec
        }
        params.update(kwargs)

        params_url = urllib.parse.urlencode(params)

        url = urllib.parse.urljoin(url, path)
        url += "?" + params_url

        return url

    def get_favorites(self,
                      user_id: str,
                      token: str,
                      media_type: Optional[MediaType] = None,
                      **kwargs) -> dict:
        params = {
            "Filters": "IsFavorite",
            "Recursive": True,
        }
        params.update(kwargs)

        if media_type:
            params["IncludeItemTypes"] = media_type.value

        url = self.server_endpoint + f"/Users/{user_id}/Items"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers, params=params)

        if res:
            json_res = json.loads(res.content)
            return json_res["Items"]
        else:
            res.raise_for_status()

    def get_playlist(self,
                     user_id: str,
                     token: str,
                     playlist_name: Optional[str] = None,
                     **kwargs):
        params = {
            "IncludeItemTypes": "Playlist",
            "Recursive": True
        }
        params.update(kwargs)

        if playlist_name:
            params["searchTerm"] = playlist_name

        url = self.server_endpoint + f"/Users/{user_id}/Items"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers, params=params)

        if res:
            json_res = json.loads(res.content)
            return json_res["Items"]
        else:
            res.raise_for_status()

    def get_playlist_items(self,
                           user_id: str,
                           token: str,
                           playlist_id: str,
                           **kwargs):
        params = {
            "UserId": user_id
        }
        params.update(kwargs)

        url = self.server_endpoint + f"/Playlists/{playlist_id}/Items"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers, params=params)

        if res:
            json_res = json.loads(res.content)
            return json_res["Items"]
        else:
            res.raise_for_status()

    def search_media_items(self,
                           user_id: str,
                           token: str,
                           term: str,
                           media: MediaType,
                           limit=20,
                           **kwargs):
        params = {
            "searchTerm": term,
            "Recursive": True,
            "IncludeItemTypes": media.value,
            "Limit": limit
        }
        params.update(kwargs)

        url = self.server_endpoint + f"/Users/{user_id}/Items"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers, params=params)

        if res:
            json_res = json.loads(res.content)
            return json_res["Items"]
        else:
            res.raise_for_status()

    def get_artist_items(self,
                         user_id: str,
                         token: str,
                         artist_id: str,
                         media: MediaType,
                         **kwargs):
        params = {
            "ArtistIds": artist_id,
            "Recursive": True,
            "MediaTypes": media.value,
        }
        params.update(kwargs)

        url = self.server_endpoint + f"/Users/{user_id}/Items"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers, params=params)

        if res:
            json_res = json.loads(res.content)
            return json_res["Items"]
        else:
            res.raise_for_status()

    def search_artist(self,
                      user_id: str,
                      token: str,
                      term, **kwargs):
        params = {
            "UserId": user_id,
            "searchTerm": term,
            "IncludeArtists": True,
            "Recursive": True
        }
        params.update(kwargs)

        url = self.server_endpoint + "/Artists"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers, params=params)

        if res:
            json_res = json.loads(res.content)
            return json_res["Items"]
        else:
            res.raise_for_status()

    def get_recently_added(self, user_id: str, token=str, media=None, limit=50, **kwargs):
        params = {
            "Limit": limit
        }
        params.update(kwargs)

        if media:
            params["IncludeItemTypes"] = media.value

        url = self.server_endpoint + f"/Users/{user_id}/Items/Latest"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers, params=params)

        if res:
            return json.loads(res.content)
        else:
            res.raise_for_status()

    def favorite(self, user_id: str, token: str, media_id: str):
        url = self.server_endpoint + f"/Users/{user_id}/FavoriteItems/{media_id}"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.post(url, headers=headers)

        if res:
            return json.loads(res.content)
        else:
            res.raise_for_status()

    def unfavorite(self, user_id: str, token: str, media_id: str):
        url = self.server_endpoint + f"/Users/{user_id}/FavoriteItems/{media_id}"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.delete(url, headers=headers)

        if res:
            return json.loads(res.content)
        else:
            res.raise_for_status()
