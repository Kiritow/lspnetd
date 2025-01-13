import base64
import json
import time
from typing import Any
import requests
from lspnetd.secure.channel import SecureChannelClient
from lspnetd.secure.message import SecureMessage
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from pydantic import BaseModel


class HandshakeResponseSchema(BaseModel):
    cid: int
    key: str
    sign: str
    data: str


class SecureChannelHTTPClient:
    def __init__(self, client_hostname: str, domain: str, 
                 client_private_sign_key_der_bytes: bytes,
                 peer_public_sign_key_der_bytes: bytes):
        self.name = client_hostname
        self.domain = domain
        self.issue_at = 0
        self.expire_at = 0

        client_private_sign_key = serialization.load_der_private_key(client_private_sign_key_der_bytes, None)
        peer_public_sign_key = serialization.load_der_public_key(peer_public_sign_key_der_bytes)

        assert isinstance(client_private_sign_key, Ed25519PrivateKey), "invalid client private sign key"
        assert isinstance(peer_public_sign_key, Ed25519PublicKey), "invalid peer public sign key"

        self.channel = SecureChannelClient(client_private_sign_key, peer_public_sign_key)
    
    def get_persistent_state(self) -> bytes:
        if self.issue_at == 0:
            return b""
        
        return self.issue_at.to_bytes(8, 'big') + self.expire_at.to_bytes(8, 'big') + self.channel.connection_id.to_bytes(8, 'big') + self.channel.shared_secret

    def load_persistent_state(self, state: bytes):
        self.issue_at = int.from_bytes(state[:8], 'big')
        self.expire_at = int.from_bytes(state[8:16], 'big')
        self.channel.connection_id = int.from_bytes(state[16:24], 'big')
        self.channel.shared_secret = state[24:]
        self.channel.handshake_private_key = None

    def handshake(self):
        handshake_bytes, handshake_sign_bytes = self.channel.get_handshake()
        r = requests.post(f"https://{self.domain}/node/connect", json={
            "name": self.name,
            "key": base64.b64encode(handshake_bytes).decode(),
            "sign": base64.b64encode(handshake_sign_bytes).decode(),
        })
        response = HandshakeResponseSchema.model_validate_json(r.content)
        self.channel.complete_handshake(
            peer_public_key_bytes=base64.b64decode(response.key),
            peer_public_key_sign_bytes=base64.b64decode(response.sign),
            connection_id=response.cid)

        first_sec_message = SecureMessage.from_bytes(base64.b64decode(response.data))
        raw_bytes = self.channel.decrypt(first_sec_message)
        first_message = json.loads(raw_bytes)
        self.issue_at = int(first_message["iat"])
        self.expire_at = int(first_message["exp"])

    def ensure(self):
        if time.time() + 60 < self.expire_at:
            return
        
        self.issue_at = 0
        self.expire_at = 0
        self.channel.reset()
        self.handshake()

    def send(self, data: dict[Any, Any]):
        self.ensure()
        plaintext_bytes = json.dumps(data).encode()
        sec_message = self.channel.encrypt(plaintext_bytes)
        payload = base64.b64encode(sec_message.to_bytes()).decode()

        r = requests.post(f"https://{self.domain}/node/send", data=payload)
        response_bytes = base64.b64decode(r.content)

        sec_message = SecureMessage.from_bytes(response_bytes)
        plaintext_bytes = self.channel.decrypt(sec_message)
        return json.loads(plaintext_bytes)
