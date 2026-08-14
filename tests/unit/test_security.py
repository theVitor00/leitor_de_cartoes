"""
Unit tests for QR Code payload security hashing and verification.
"""

import unittest
from omr_app.core.security import generate_qr_payload, verify_and_decode_qr_payload


class TestSecurityPayload(unittest.TestCase):

    def test_generate_and_verify_valid_payload(self):
        prova_id = 42
        aluno_id = 101

        payload_str = generate_qr_payload(prova_id, aluno_id)
        self.assertIsInstance(payload_str, str)
        self.assertIn('"p":42', payload_str)
        self.assertIn('"a":101', payload_str)

        is_valid, p_id, a_id = verify_and_decode_qr_payload(payload_str)
        self.assertTrue(is_valid)
        self.assertEqual(p_id, prova_id)
        self.assertEqual(a_id, aluno_id)

    def test_tampered_payload_verification(self):
        prova_id = 42
        aluno_id = 101

        # Tampered hash
        tampered_json = '{"p":42,"a":101,"h":"0000000000"}'
        is_valid, p_id, a_id = verify_and_decode_qr_payload(tampered_json)
        self.assertFalse(is_valid)
        self.assertEqual(p_id, 42)
        self.assertEqual(a_id, 101)

    def test_invalid_json_payload(self):
        is_valid, p_id, a_id = verify_and_decode_qr_payload("invalid json content")
        self.assertFalse(is_valid)
        self.assertEqual(p_id, 0)
        self.assertEqual(a_id, 0)


if __name__ == "__main__":
    unittest.main()
