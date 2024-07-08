import time
import hmac
import random
import json
import typing
import hashlib
import requests
import datetime
import logging
from base64 import b64encode, b64decode
from .validation import BaseURLLiteral, ClientBaseURLType


class LMAXClient:
    """LMAX Base Client that provides authentication and request method to interact with the LMAX API.
    Rate limiting is also implemented to avoid hitting the rate limit of the LMAX API of 1 request per second.

    Raises:
    - ValueError: If the base_url is not provided for live environment, if using is_demo flag you don't need to provide base_url

    Returns:
    - LMAXClient: An instance of the LMAXClient object
    """

    client_key_id: typing.Optional[str]
    secret: typing.Optional[str]
    base_url: BaseURLLiteral
    token: str
    last_request_time: float

    def __init__(
        self,
        client_key_id: typing.Optional[str] = None,
        secret: typing.Optional[str] = None,
        base_url: BaseURLLiteral = None,
        rate_limit_seconds: int = 1,
        verbose: bool = False,
    ):
        """Initialise the LMAXClient object. This will authenticate the client and store the token as an attribute.

        Args:
            client_key_id (str): LMAX API key
            secret (str): LMAX API secret
            base_url (_type_, optional): LMAX API endpoint to use.
            is_demo (bool, optional): Flag to use the demo endpoint url. Defaults to False.
            verbose (bool, optional): Flag to set verbose logging of requests and responses. Defaults to False.
        """

        # Store the input parameters as attributes
        self.verbose = verbose
        self.client_key_id = client_key_id
        self.secret = secret
        self.base_url = base_url
        self.is_demo = True if "demo" in base_url.lower() else False
        self.rate_limit_seconds = rate_limit_seconds
        self.last_request_time = 0

        log_level = logging.DEBUG if self.verbose else logging.INFO
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        self.logger.addHandler(logging.StreamHandler())
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        self.logger.handlers[0].setFormatter(formatter)

        # If base_url is not provided for live environment, raise an error
        if not base_url:
            self.logger.error(
                "You need to provide the base_url for live environment. Please refer to the documentation for more information."
            )
            ClientBaseURLType.dict()
            raise ValueError("You need to provide the base_url")

        # Authenticate and store the token as an attribute
        if self.client_key_id and self.secret:
            self.token = self._authenticate()

    def _generate_signature(self, timestamp, nonce):
        # Decode the secret as it's base64 encoded
        secret_decoded = b64decode(self.secret)
        # The correct order is client_key_id + nonce + timestamp
        message = f"{self.client_key_id}{nonce}{timestamp}".encode("utf-8")
        # Sign the message using HMAC SHA256
        signature = hmac.new(secret_decoded, message, hashlib.sha256).digest()
        # Return the base64 encoded signature
        return b64encode(signature).decode("utf-8")

    def _authenticate(self):
        endpoint = "/v1/authenticate"
        # Generate timestamp with millisecond resolution
        timestamp = (
            datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        )
        nonce = str(random.randint(0, int(1e16)))
        signature = self._generate_signature(timestamp, nonce)

        payload = {
            "client_key_id": self.client_key_id,
            "timestamp": timestamp,
            "nonce": nonce,
            "signature": signature,
        }

        headers = {"Content-Type": "application/json"}

        # Rate limit the authentication request
        self.wait_for_rate_limit()

        # Make the authentication request and handle HTTP errors (rate limit)
        count = 0
        while count < 3:
            try:
                response = requests.post(
                    self.base_url + endpoint,
                    data=json.dumps(payload),
                    headers=headers,
                    timeout=5,
                )
                if response.status_code == 200:
                    return response.json()["token"]
            except requests.exceptions.HTTPError as e:
                self.logger.error(e)
                time.sleep(1)

        raise ValueError("Failed to authenticate after 3 attempts")

    def _request(
        self,
        endpoint: str,
        method="GET",
        params: typing.Dict[str, str] = None,
        payload: typing.Dict[str, str] = None,
        authenticated: bool = False,
    ) -> typing.Dict[str, typing.Any]:
        """Function to make a request to the LMAX API.

        Args:
            endpoint (str): LMAX API endpoint to use.
            method (str, optional): HTTP Request method type. Defaults to "GET".
            params (typing.Dict[str, str], optional): The parameters to send in the request. Defaults to None.
            payload (typing.Dict[str, str], optional): The data to send in the request. Defaults to None.
            authenticated (bool, optional): Flag indicating if the request requires authentication. Defaults to True.

        Returns:
            typing.Dict[str, typing.Any]: The response from the LMAX API
        """
        self.wait_for_rate_limit()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}" if authenticated else None,
        }
        response = requests.request(
            method,
            self.base_url + endpoint,
            params=params,
            data=json.dumps(payload) if payload else None,
            headers=headers,
            timeout=5,
        )
        self.last_request_time = time.time()

        if self.verbose:
            self.logger.debug("Request:    %s", response.request.url)
            self.logger.debug("Headers:    %s", response.request.headers)
            self.logger.debug("Payload:    %s", response.request.body)
            self.logger.debug("Response:   %s", response.text)

        if authenticated and response.status_code == 401:
            self.token = self._authenticate()  # Refresh token
            headers["Authorization"] = (
                f"Bearer {self.token}"  # Update headers with new token
            )

            self.wait_for_rate_limit()

            response = requests.request(  # Retry the request with the new token
                method,
                self.base_url + endpoint,
                params=params,
                data=json.dumps(payload) if payload else None,
                headers=headers,
                timeout=5,
            )
            if self.verbose:
                self.logger.debug("Request:    %s", response.request.url)
                self.logger.debug("Headers:    %s", response.request.headers)
                self.logger.debug("Payload:    %s", response.request.body)
                self.logger.debug("Response:   %s", response.text)

        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def wait_for_rate_limit(self):
        """Function to wait for the rate limit to expire."""
        current_time = time.time()
        time_diff = current_time - self.last_request_time
        if time_diff < self.rate_limit_seconds:
            time.sleep(self.rate_limit_seconds - time_diff)
