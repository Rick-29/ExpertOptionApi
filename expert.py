from api.backend.client import WebSocketClient
import asyncio
import logging
from collections import defaultdict, OrderedDict
from threading import Thread
import threading
import ssl
import time
import simplejson as json
import pause
import websocket
import decimal
import urllib
from websocket._exceptions import WebSocketConnectionClosedException

from api.backend.ws.channels.ping import Ping


import api.global_values as global_value
from api.constants import BasicData, Symbols

class EoApi:
    def __init__(self, token: str, server_region):
        self.token = token
        self.server_region = server_region

        self.websocket_client = WebSocketClient(api=self, token=self.token)  # Composition
        # Set logging level and format
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')

        # Create file handler and add it to the logger
        file_handler = logging.FileHandler('expert.log')
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)


        self.logger.info("Initializing EoApi with token: %s, region: %s", token, server_region)

        self.websocket_thread = None
        self.profile = None
        self.message_callback = None
        self._request_id = 1
        self.results = self.FixSizeOrderedDict(max=300)
        self.msg_by_ns = self.FixSizeOrderedDict(max=300)
        self.msg_by_action = self.nested_dict(1, lambda: self.FixSizeOrderedDict(max=300))

        self.ping_thread = threading.Thread(target=self.auto_ping)  # Create a new thread for auto_ping
        self.ping_thread.daemon = True  # Set the thread as a daemon so it will terminate when the main program terminates
        self.ping_thread.start()  # Start the auto_ping thread

        self.websocket_client.wss.run_forever()

    def Profile(self):
        self.logger.info("Fetching profile")
        global_value.is_profile = True
        self.send_websocket_request(action="multipleAction",
                                    msg=BasicData.SendData(self),
                                    ns="_common")
        return global_value.ProfileData
    def Buy(self, amount, type, assetid, exptime, isdemo, strike_time):
        try:
            self.logger.info("Buying...")
            print("Buying...") # replace in prod
            self.send_websocket_request(action="BuyOption", msg=BasicData.BuyData(self=self, amount=amount, type=type, assetid=assetid, exptime=exptime, isdemo=isdemo, strike_time=strike_time), ns=300)
            return global_value.BuyData
        except WebSocketConnectionClosedException as e:
            print(f"Error: {e}")
            self.websocket_client.wss.close()
            self.connect()
            self.logger.info("Buying...")
            print("Buying...") # replace in prod
            self.send_websocket_request(action="BuyOption", msg=BasicData.BuyData(self=self, amount=amount, type=type, assetid=assetid, exptime=exptime, isdemo=isdemo, strike_time=strike_time), ns=300)
            return global_value.BuyData
    def SetDemo(self):
        data = {"action":"setContext","message":{"is_demo":1},"token": self.token,"ns":1}
        self.send_websocket_request(action="setContext", msg=data, ns="_common")
        return True

    def connect(self):
        global_value.check_websocket_if_connect = None

        self.websocket_client = WebSocketClient(self, token=self.token)

        self.websocket_thread = threading.Thread(target=self.websocket_client.wss.run_forever, kwargs={
            'sslopt': {
                "check_hostname": False,
                "cert_reqs": ssl.CERT_NONE,
                "ca_certs": "cacert.pem"
            },
            "ping_interval": 0,
            'skip_utf8_validation': True,
            "origin": "https://app.expertoption.com",
            # "http_proxy_host": '127.0.0.1', "http_proxy_port": 8890
        })

        self.websocket_thread.daemon = True
        self.websocket_thread.start()

        # self.authorize(authorize=self.token)

        # TODO support it
        # self.multiple_action(actions=[
        #     self.get_countries(json=True),
        #     self.get_currency(json=True),
        #     self.get_profile(json=True),
        #     self.get_environment(json=True),
        #     self.get_open_options(json=True),
        #     self.get_user_group(json=True),
        #     self.get_set_time_zone(json=True),
        #     self.get_history_steps(json=True),
        #     self.get_trade_history(json=True),
        # ], ns="_common")

        self.websocket_client.wss.keep_running = True

        while True:
            try:
                if global_value.check_websocket_if_connect == 0 or global_value.check_websocket_if_connect == -1:
                    return False
                elif global_value.check_websocket_if_connect == 1:
                    break
            except Exception:
                pass
            pass

        self.send_websocket_request(action="multipleAction",
                                    msg={"token": self.token, "v": 18, "action": "multipleAction",
                                         "message": {"token": self.token, "actions": [
                                             {"action": "getCountries", "message": None, "ns": None, "v": 18,
                                              "token": self.token},
                                             {"action": "getCurrency", "message": None, "ns": None, "v": 18,
                                              "token": self.token},
                                             {"action": "profile", "message": None, "ns": None, "v": 18,
                                              "token": self.token},
                                             {"action": "environment", "message": None, "ns": None, "v": 18,
                                              "token": self.token}, {"action": "assets",
                                                                     "message": {"mode": ["vanilla", "binary"],
                                                                                 "subscribeMode": ["vanilla"]},
                                                                     "ns": None, "v": 18, "token": self.token},
                                             {"action": "openOptions", "message": None, "ns": None, "v": 18,
                                              "token": self.token},
                                             {"action": "userGroup", "message": None, "ns": None, "v": 18,
                                              "token": self.token},
                                             {"action": "setTimeZone", "message": {"timeZone": 360}, "ns": None,
                                              "v": 18, "token": self.token},
                                             {"action": "historySteps", "message": None, "ns": None, "v": 18,
                                              "token": self.token}, {"action": "tradeHistory",
                                                                     "message": {"mode": ["binary", "vanilla"],
                                                                                 "count": 100, "index_from": 0},
                                                                     "ns": None, "v": 18, "token": self.token}]}},
                                    ns="_common")
        start_t = time.time()
        self.logger.info("WebSocket connected")
        return True
    def auto_ping(self):
        self.logger.info("Starting auto ping thread")

        while True:
            pause.seconds(5)  # Assuming that you've imported 'pause'
            try:
                if self.websocket_client.wss.sock and self.websocket_client.wss.sock.connected:  # Check if socket is connected
                    self.ping()
                else:
                    self.logger.warning("WebSocket is not connected. Attempting to reconnect.")
                    # Attempt reconnection
                    if self.connect():
                        self.logger.info("Successfully reconnected.")
                    else:
                        self.logger.warning("Reconnection attempt failed.")
                    try:
                        self.ping()
                        self.logger.info("Sent ping reuqests successfully!")
                    except Exception as e:
                        self.logger.error(f"A error ocured trying to send ping: {e}")
            except Exception as e:  # Catch exceptions and log them
                self.logger.error(f"An error occurred while sending ping or attempting to reconnect: {e}")
                try:
                    self.logger.warning("Trying again...")
                    v1 = self.connect()
                    if v1:
                        self.logger.info("Conection completed!, sending ping...")
                        self.ping()
                    else:
                        self.logger.error("Connection was not established")
                except Exception as e:
                    self.logger.error(f"A error ocured when trying again: {e}")

            pause.seconds(5)  # Assuming that you've imported 'pause'


    def send_websocket_request(self, action: str, msg, ns: str = None):
        """Send websocket request to ExpertOption server.
        :type action: str
        :param ns: str
        :param dict msg: The websocket request msg.
        """
        self.logger.debug("Sending WebSocket request: action=%s, ns=%s", action, ns)

        if ns is not None and not ns:
            ns = self.request_id

        msg['ns'] = ns

        if ns:
            # self.results[ns] = None
            self.msg_by_ns[ns] = None
            self.msg_by_action[action][ns] = None

        def default(obj):
            if isinstance(obj, decimal.Decimal):
                return str(obj)
            raise TypeError

        data = json.dumps(msg, default=default)
        self.logger.debug(data)

        self.websocket_client.wss.send(bytearray(urllib.parse.quote(data).encode('utf-8')), opcode=websocket.ABNF.OPCODE_BINARY)
        pause.seconds(5)
        return ns

    def nested_dict(self, n, type):
        if n == 1:
            return defaultdict(type)
        else:
            return defaultdict(lambda: self.nested_dict(n - 1, type))
    @property
    def request_id(self):
        self._request_id += 1
        return str(self._request_id - 1)

    @property
    def ping(self):
        self.logger.info("Sent a ping request")
        return Ping(self).__call__

    class FixSizeOrderedDict(OrderedDict):
        def __init__(self, *args, max=0, **kwargs):
            self._max = max
            super().__init__(*args, **kwargs)

        def __setitem__(self, key, value):
            OrderedDict.__setitem__(self, key, value)
            if self._max > 0:
                if len(self) > self._max:
                    self.popitem(False)


class _api:
    def __init__(self, token: str) -> None:
        self.token = token

    def _profile(self):

        # Assuming WebSocketClient is set up to handle this data
        # WebSocket loop should probably not be here.
        # You should start it in your main function or some entry point.
        return {"Response": "Success"}
