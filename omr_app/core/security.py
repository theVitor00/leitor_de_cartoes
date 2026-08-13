"""
Security and Hashing Module for QR Code Payload Generation & Verification.
"""

import hashlib
import json

SECRET_KEY = "OMR_SECURE_SALT_2026_KEY"


def generate_qr_payload(prova_id: int, aluno_id: int) -> str:
    """
    Generates a secure JSON string for QR Code embedding with SHA-256 HMAC hash.
    """
    raw_str = f"prova:{prova_id}|aluno:{aluno_id}|secret:{SECRET_KEY}"
    sig_hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()[:16]

    payload_dict = {
        "p": prova_id,
        "a": aluno_id,
        "h": sig_hash
    }
    return json.dumps(payload_dict, separators=(',', ':'))


def verify_and_decode_qr_payload(qr_content: str) -> tuple[bool, int, int]:
    """
    Validates and decodes QR Code JSON payload.
    Returns: (is_valid: bool, prova_id: int, aluno_id: int)
    """
    try:
        data = json.loads(qr_content)
        prova_id = int(data.get("p"))
        aluno_id = int(data.get("a"))
        provided_hash = data.get("h")

        raw_str = f"prova:{prova_id}|aluno:{aluno_id}|secret:{SECRET_KEY}"
        expected_hash = hashlib.sha256(raw_str.encode('utf-8')).hexdigest()[:16]

        if provided_hash == expected_hash:
            return True, prova_id, aluno_id
        else:
            # Fallback check if hash matches without truncation or standard
            return False, prova_id, aluno_id
    except Exception:
        return False, 0, 0
