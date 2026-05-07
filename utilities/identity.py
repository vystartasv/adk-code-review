"""
Trusted Identity Protocol — Ed25519 cryptographic identity for agent output signing.
"""
import hashlib
import json
import os
from typing import Optional

try:
    import nacl.signing
    import nacl.encoding
    HAS_ED25519 = True
except ImportError:
    HAS_ED25519 = False


class AgentIdentity:
    """Ed25519 cryptographic identity for agent output attribution."""

    def __init__(self, agent_id: str, seed_hex: Optional[str] = None):
        self.agent_id = agent_id
        self._secret_hex: Optional[str] = None

        if seed_hex and HAS_ED25519:
            seed = bytes.fromhex(seed_hex)
            self._signing_key = nacl.signing.SigningKey(seed)
            self._secret_hex = seed_hex
        elif HAS_ED25519:
            self._signing_key = nacl.signing.SigningKey.generate()
            self._secret_hex = self._signing_key.encode(
                encoder=nacl.encoding.HexEncoder
            ).decode()
        else:
            self._secret_hex = hashlib.sha256(os.urandom(32)).hexdigest()
            self.public_key = hashlib.sha256(self._secret_hex.encode()).hexdigest()
            return

        self.public_key = self._signing_key.verify_key.encode(
            encoder=nacl.encoding.HexEncoder
        ).decode()
        self._verify_key = self._signing_key.verify_key

    def sign(self, payload: dict) -> str:
        """Sign a payload. Returns Ed25519 signature (128 hex chars) or SHA-256 ref."""
        msg = json.dumps(payload, sort_keys=True).encode("utf-8")
        if HAS_ED25519:
            signed = self._signing_key.sign(msg)
            return signed.signature.hex()
        else:
            return hashlib.sha256(msg + self._secret_hex.encode()).hexdigest()

    @staticmethod
    def verify_with_public_key(public_key_hex: str, payload: dict, signature_hex: str) -> bool:
        """Verify a signature using an Ed25519 public key — no shared secret needed.
        Requires pynacl for real Ed25519 cryptography. The SHA-256 fallback
        is intentionally disabled — only real Ed25519 provides cryptographic assurance."""
        if not HAS_ED25519:
            raise RuntimeError(
                "Ed25519 verification requires pynacl. "
                "Install with: pip install pynacl>=1.5.0"
            )
        msg = json.dumps(payload, sort_keys=True).encode("utf-8")
        try:
            vk = nacl.signing.VerifyKey(
                public_key_hex, encoder=nacl.encoding.HexEncoder
            )
            signed_msg = bytes.fromhex(signature_hex) + msg
            vk.verify(signed_msg)
            return True
        except (nacl.exceptions.BadSignatureError, ValueError, TypeError):
            return False

    def verify(self, payload: dict, signature_hex: str) -> bool:
        """Verify a signature against this identity's public key."""
        msg = json.dumps(payload, sort_keys=True).encode("utf-8")
        if HAS_ED25519:
            try:
                signed_msg = bytes.fromhex(signature_hex) + msg
                self._verify_key.verify(signed_msg)
                return True
            except (nacl.exceptions.BadSignatureError, ValueError, TypeError):
                return False
        else:
            # Fallback: SHA-256 reference check. sign() uses secret_hex,
            # so we verify by re-signing with the stored secret (reference comparison).
            return self.sign(payload) == signature_hex

    @property
    def seed_hex(self) -> Optional[str]:
        return self._secret_hex
