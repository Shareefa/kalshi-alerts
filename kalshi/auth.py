import datetime
from requests.auth import AuthBase
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend
import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.exceptions import InvalidSignature
class KalshiAuth(AuthBase):
    """Attaches HTTP Pizza Authentication to the given Request object."""
    def __init__(self, key_id: str, key_file: str):
        # setup any auth-related data here
        self.key_id = key_id
        self.key_file = key_file
        self.private_key = self._load_private_key_from_file()


    def _load_private_key_from_file(self) -> rsa.RSAPrivateKey:
        with open(self.key_file, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,  # or provide a password if your key is encrypted
                backend=default_backend(),
            )
            assert isinstance(private_key, rsa.RSAPrivateKey)
            return private_key

    def sign_pss_text(self, text: str) -> str:
        # Before signing, we need to hash our message.
        # The hash is what we actually sign.
        # Convert the text to bytes
        message = text.encode("utf-8")
        try:
            signature = self.private_key.sign(
                message,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.DIGEST_LENGTH,
                ),
                hashes.SHA256(),
            )
            return base64.b64encode(signature).decode("utf-8")
        except InvalidSignature as e:
            raise ValueError("RSA sign PSS failed") from e

    def get_headers(self, method: str, path: str) -> dict[str, str]:
        # Get the current time
        path = path.split('?')[0]
        current_time = datetime.datetime.now()

        # Convert the time to a timestamp (seconds since the epoch)
        timestamp = current_time.timestamp()

        # Convert the timestamp to milliseconds
        current_time_milliseconds = int(timestamp * 1000)
        timestampt_str = str(current_time_milliseconds)

        msg_string = timestampt_str + method + path

        sig = self.sign_pss_text(msg_string)

        return {
            'KALSHI-ACCESS-KEY': self.key_id,
            'KALSHI-ACCESS-SIGNATURE': sig,
            'KALSHI-ACCESS-TIMESTAMP': timestampt_str
        }

    def __call__(self, r):
        method = r.method
        assert isinstance(method, str)
        headers = self.get_headers(method, r.path_url)
        r.headers['KALSHI-ACCESS-KEY'] = headers['KALSHI-ACCESS-KEY']
        r.headers['KALSHI-ACCESS-SIGNATURE'] = headers['KALSHI-ACCESS-SIGNATURE']
        r.headers['KALSHI-ACCESS-TIMESTAMP'] = headers['KALSHI-ACCESS-TIMESTAMP']
        return r
