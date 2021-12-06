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
    VIDEO = "Video,MusicVideo"
    CHANNEL = "TvChannel"


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
                       **kwargs) -> Tuple[str,str]:

        """
        Generate a url which allows streaming the requested media file.

        Returns [stream_type,url]
                if stream_type="audio", url is a stream url ready for AudioPlayer
                if stream_type="video", url is a url to video to pass on to VideoApp
                if stream_type="", something went wrong
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

        stream_type = "audio"
        if play_info["MediaSources"][0]:
            for stream in play_info["MediaSources"][0]["MediaStreams"]:
                if stream["Type"] == "Video":
                    stream_type = "video"
                    break

        url = self.server_endpoint
        if stream_type == "audio":
            # prepare url for AudioPlayer
            path = f"/Audio/{item_id}/universal"
            params = {
                'UserId': user_id,
                'DeviceId': device_id,
                "MaxStreamingBitrate": max_streaming_bitrate,
                "PlaySessionId": play_info["PlaySessionId"],
                "api_key": token,
                "AudioCodec": audio_codec
            }

        elif stream_type == "video":
            # prepare url for VideoApp
            path = f"/Videos/{item_id}/stream"
            params = {
                "Container" : play_info["MediaSources"][0]["Container"],
                "Tag": play_info["MediaSources"][0]["ETag"],
                "PlaySessionId": play_info["PlaySessionId"],
                'DeviceId': device_id,
                "api_key": token
            }

        params.update(kwargs)

        params_url = urllib.parse.urlencode(params)

        url = urllib.parse.urljoin(url, path)
        url += "?" + params_url
        return stream_type, url


    def get_ancestor_with_image(self,
                    item_id: str,
                    token: str) -> str:

        """
        Returns id of the first ancestor of item_id that has an image
        Return empty string (None) if: * there are no ancestors, or
                                       * no ancestor has an image
        """

        url = self.server_endpoint + f"/Items/{item_id}/Ancestors"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers)
        if res:
            ancestor_info = json.loads(res.content)
            if not ancestor_info:
                # item has no ancestors
                return None
        else:
            res.raise_for_status()

        # return the first ancestor we find with an image
        for ancestor in ancestor_info:
            if ancestor["ImageTags"]:
                return ancestor["Id"]

        return None


    def get_art_url(self,
                    item_id: str,
                    token: str,
                    **kwargs) -> str:
        """
        Generate a url to display cover art for this item
        Return empty string (None) if there is no cover art available
        """

        # first check if there is any cover art
        url = self.server_endpoint + f"/Items/{item_id}/Images"

        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": self._build_emby_auth_header(token=token)
        }

        res = requests.get(url, headers=headers)
        if res:
            image_info = json.loads(res.content)
            if not image_info:
                # this item has no image - use an ancestor's image (if there is one)
                parent_id = self.get_ancestor_with_image(item_id=item_id,token=token)
                if parent_id:
                    # RECURSIVELY call get_art_url() to serve up the image
                    return self.get_art_url(item_id=parent_id,token=token)

                # no image to display
                return None
        else:
            res.raise_for_status()

        # prefer the "Primary" image, otherwise we'll use the first image (image_info[0]) in the list of images
        image_index = 0
        idx = 0
        for info in image_info:
            if info["ImageType"] == "Primary":
                image_index = idx
                break
            idx += 1

        # build url
        url = self.server_endpoint
        image_type = image_info[image_index]["ImageType"]
        path = f"/Items/{item_id}/Images/{image_type}"
        url = urllib.parse.urljoin(url, path)

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
