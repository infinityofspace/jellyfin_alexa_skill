import json
import threading

from websocket import WebSocketApp


class JellyfinSocket(WebSocketApp):
    """
    Class to handle websocket connection to a Jellyfin server.
    It implements the keepalive and websocket message parsing logic.
    """

    def __init__(self, url: str,
                 on_message: callable = None,
                 on_error: callable = None,
                 on_close: callable = None,
                 on_open: callable = None) -> None:
        """
        Initialize the websocket connection to the Jellyfin server.

        :param url: The url of the websocket server.
        :param on_message: The callback to call when a message is received from the websocket server.
        :param on_error: The callback to call when an error occurs.
        :param on_close: The callback to call when the websocket connection is closed.
        :param on_open: The callback to call when the websocket connection is opened.
        """

        super().__init__(url,
                         on_message=self._on_message,
                         on_error=on_error,
                         on_close=self._on_close,
                         on_open=on_open)

        self.on_message_callback = on_message
        self.on_close_callback = on_close
        self.stop_event = threading.Event()
        self.keep_alive_thread = None

    def _on_close(self, sock, status_code, message) -> None:
        """
        Callback for when the websocket connection is closed.
        Call the provided on_close callback if it exists.

        :param sock: The websocket connection.
        :param status_code: The status code of the websocket connection.
        :param message: The message of the websocket connection.
        """

        if self.on_close_callback:
            self.on_close_callback(self, status_code, message)

        # stop the keep alive thread
        self.stop_event.set()
        if self.keep_alive_thread:
            self.keep_alive_thread.join()

    def _on_message(self, sock, message) -> None:
        """
        Callback for when a message is received from the websocket server.

        :param sock: The websocket connection.
        :param message: The message received from the websocket server.
        """

        message = json.loads(message)

        data = message.get("Data", {})

        if message["MessageType"] == "ForceKeepAlive":
            self.send("ForceKeepAlive")

            # stop previous keep alive thread
            if self.keep_alive_thread:
                self.stop_event.set()
                self.keep_alive_thread.join()

            def keep_alive(timeout):
                wait_timeout = timeout / 2
                # keep sending the keep alive message until we get the stop event
                while not self.stop_event.is_set():
                    if self.stop_event.wait(wait_timeout):
                        break
                    else:
                        self.send("ForceKeepAlive")

            self.keep_alive_thread = threading.Thread(target=keep_alive, args=(data,))
            self.keep_alive_thread.start()

            return
        elif message["MessageType"] == "KeepAlive":
            return

        if self.on_message_callback:
            self.on_message_callback(self, message["MessageType"], data)

    def send(self, message_type, data: dict = None) -> None:
        """
        Send a message to the websocket server.

        :param message_type: The type of message to send.
        :param data: The data to send with the message.
        """

        message = json.dumps({'MessageType': message_type, "Data": data})
        super().send(message)
