from enum import Enum
from urllib.parse import urlparse


class Protocols(Enum):
    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"
    FTP = "ftp"
    SFTP = "sftp"
    FTPS = "ftps"


SECURE_PROTOCOLS = [Protocols.HTTPS, Protocols.WSS, Protocols.SFTP, Protocols.FTPS]


def validate_url(url: str, proto: Protocols = None, encrypted: bool = False) -> bool:
    """
    Validate the URL.

    :param url: URL to validate
    :param proto: Protocol of which the URL should be
    :param encrypted: whether the URL have to be the encrypted version of the protocol

    :return: True if the URL is valid, False otherwise
    """

    try:
        result = urlparse(url)
        if proto and result.scheme != proto.value:
            return False
        if encrypted and result.scheme not in SECURE_PROTOCOLS:
            return False
        return all([result.scheme, result.netloc])
    except ValueError:
        return False
