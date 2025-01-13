from dataclasses import dataclass


@dataclass
class SecureMessage:
    cid: int  # max 8 bytes, 2^64
    timestamp: int
    # HKDF
    salt: bytes
    # AES256GCM
    ciphertext: bytes
    nonce: bytes
    tag: bytes
    # Signature of plaintext
    signature: bytes

    def get_bytes_to_sign(self) -> bytes:
        return self.cid.to_bytes(8, 'big') + self.timestamp.to_bytes(8, 'big') + self.salt + self.nonce + self.tag + self.ciphertext

    def to_bytes(self) -> bytes:
        return self.signature + self.cid.to_bytes(8, 'big') + self.timestamp.to_bytes(8, 'big') + self.salt + self.nonce + self.tag + self.ciphertext

    @classmethod
    def from_bytes(cls, data: bytes):
        signature = data[:64]
        cid = int.from_bytes(data[64:72], 'big')
        timestamp = int.from_bytes(data[72:80], 'big')
        salt = data[80:112]
        nonce = data[112:124]
        tag = data[124:140]
        ciphertext = data[140:]
        return cls(cid, timestamp, salt, ciphertext, nonce, tag, signature)
