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
    ALBUM = "MusicAlbum"


class JellyfinClient:
    """
    Client for the Jellyfin API.
    """

    def __init__(self, server_endpoint: str, client_name: str = APP_NAME):
        """
        :param server_endpoint: url of the server
        :param client_name: name of the client (default: "jellyfin_alexa_skill")
        """

        self.server_endpoint = server_endpoint
        self.client_name = client_name

    @staticmethod
    def _build_emby_auth_header(client_name: str = APP_NAME,
                                device_name: str = "NONE",
                                device_id: str = "NONE",
                                version: str = __version__,
                                token: str = None) -> str:
        """
        Builds the Emby authorization header.

        :param client_name: name of the client (default: "jellyfin_alexa_skill")
        :param device_name: name of the device (default: "NONE")
        :param device_id: id of the device (default: "NONE")
        :param version: version of the client (default: __version__)
        :param token: authentication token (default: None)

        :return: string with the authorization header
        """

        header = f"MediaBrowser Client={client_name}, Device={device_name}, DeviceId={device_id}, Version={version}"

        if token:
            header += ", Token={}".format(token)

        return header

    def public_info(self) -> Optional[dict]:
        """
        Returns public information about the server.

        :return: dict with server info or None if the server is not reachable or the server can not be reached
        """

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
        """
        Get authentication token for a user.

        :param username: username of the user
        :param password: password of the user

        :return: tuple of type (user_id, token)
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
                       **kwargs) -> Tuple[str, str]:
        """
        Generate a url which allows streaming the requested media file.

        :param user_id: user id
        :param token: authentication token
        :param item_id: item id
        :param device_id: device id (default: "NONE")
        :param audio_codec: audio codec (default: "mp3")
        :param max_streaming_bitrate: max streaming bitrate (default: 140000000)
        :param start_time_ticks: start time ticks in ms (default: 0)
        :param kwargs: additional parameters passed to the server for the request

        :return: tuple of type (stream_type, url)
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong

        stream_type can be one of the following:
            "audio" - url is a stream url ready for AudioPlayer
            "video" - url is a url to video to pass on to VideoApp
            "livetv" - url is a url to stream LiveTV to VideoApp
            "" - something went wrong
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
                    if play_info["MediaSources"][0]["IsInfiniteStream"] == True:
                        stream_type = "livetv"
                    else:
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
                "Container": play_info["MediaSources"][0]["Container"],
                "PlaySessionId": play_info["PlaySessionId"],
                'DeviceId': device_id,
                "api_key": token
            }
        elif stream_type == "livetv":
            # just return the direct internet path to the live tv channel (we don't need to use Jellyfin)
            return stream_type, play_info["MediaSources"][0]["Path"]

        params.update(kwargs)

        params_url = urllib.parse.urlencode(params)

        url = urllib.parse.urljoin(url, path)
        url += "?" + params_url
        return stream_type, url

    def get_ancestor_with_image(self,
                                item_id: str,
                                token: str) -> Optional[str]:

        """
        Returns id of the first ancestor of item_id that has an image

        :param item_id: item id
        :param token: authentication token

        :return: id of the first ancestor of item_id that has an image or empty string if no such ancestor exists or no
                 ancestor has an image
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
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
                    token: str) -> Optional[str]:
        """
        Generate a url to display cover art for this item.

        :param item_id: item id
        :param token: authentication token

        :return: url to display cover art for this item or None if there is no cover art available
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
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
                parent_id = self.get_ancestor_with_image(item_id=item_id, token=token)
                if parent_id:
                    # RECURSIVELY call get_art_url() to serve up the image
                    return self.get_art_url(item_id=parent_id, token=token)

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
        """
        Get all favorite items for a specified user.

        :param user_id: user id of the user whose favorite items should be retrieved
        :param token: authentication token
        :param media_type: media type of the favorite items to retrieve
        :param kwargs: additional parameters to pass to the server for the request

        :return: dict of favorite items
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
                     **kwargs) -> dict:
        """
        Get a specified playlist.

        :param user_id: user id of the user whose playlist should be retrieved
        :param token: authentication token
        :param playlist_name: name of the playlist to retrieve
        :param kwargs: additional parameters to pass to the server for the request

        :return: dict of the playlist
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
                           **kwargs) -> dict:
        """
        Get all items in a specified playlist.

        :param user_id: user id of the user whose playlist items should be retrieved
        :param token: authentication token
        :param playlist_id: id of the playlist whose items should be retrieved
        :param kwargs: additional parameters to pass to the server for the request

        :return: dict of playlist items
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
                           limit: int = 20,
                           **kwargs) -> dict:
        """
        Search for media items.

        :param user_id: user id of the user whose media items should be searched
        :param token: authentication token
        :param term: search term
        :param media: media type to search for
        :param limit: maximum number of results to return (default: 20)
        :param kwargs: additional parameters to pass to the server for the request

        :return: dict of media items
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
        """
        Get all items of a specified artist.

        :param user_id: user id of the user whose artist items should be retrieved
        :param token: authentication token
        :param artist_id: id of the artist whose items should be retrieved
        :param media: media type to search for
        :param kwargs: additional parameters to pass to the server for the request

        :return: dict of artist items
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
                      term: str,
                      **kwargs):
        """
        Search for a specific artist.

        :param user_id: user id of the user whose artist should be searched
        :param token: authentication token
        :param term: search term
        :param kwargs: additional parameters to pass to the server for the request

        :return: dict of artist items
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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

    def get_album_items(self,
                        user_id: str,
                        token: str,
                        album_id: str) -> dict:
        """
        Get all items of a specified album.

        :param user_id: user id of the user whose album items should be retrieved
        :param token: authentication token
        :param album_id: id of the album whose items should be retrieved

        :return: dict of album items
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

        params = {
            "IncludeItemTypes": "Audio",
            "Recursive": True,
            "sortBy": "SortName",
            "ParentId": album_id
        }
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

    def get_recently_added(self,
                           user_id: str,
                           token: str,
                           media: MediaType = None,
                           limit: int = 50,
                           **kwargs) -> dict:
        """
        Get recently added items.

        :param user_id: user id of the user whose recently added items should be retrieved
        :param token: authentication token
        :param media: media type to search for (default: None = all media types)
        :param limit: maximum number of items to retrieve (default: 50)
        :param kwargs: additional parameters to pass to the server for the request

        :return: dict of recently added items
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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

    def favorite(self, user_id: str, token: str, media_id: str) -> dict:
        """
        Favorite an item.

        :param user_id: user id of the user whose item should be favorited
        :param token: authentication token
        :param media_id: id of the item to favorite

        :return: dict of the favorited item
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
        """
        Unfavorite an item.

        :param user_id: user id of the user whose item should be unfavorited
        :param token: authentication token
        :param media_id: id of the item to unfavorite

        :return: dict of the unfavorited item
        :raises: requests.exceptions.HTTPError types if the server is not reachable or something went wrong
        """

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
