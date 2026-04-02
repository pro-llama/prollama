"""Tests for NLP-based PII detection layer."""

from prollama.anonymizer.nlp_layer import NLPAnonymizer


class TestNLPAnonymizer:
    """Tests for heuristic PII detection in comments."""

    def test_detects_author_name(self):
        code = "# Author: Jan Kowalski\ndef foo(): pass\n"
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "Jan Kowalski" not in result
        assert any(m.original == "Jan Kowalski" for m in mappings)
        assert any(m.category == "PERSON" for m in mappings)

    def test_detects_created_by(self):
        code = "# Created by: Anna Nowak\nclass Foo: pass\n"
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "Anna Nowak" not in result

    def test_detects_fixed_by(self):
        code = "# Fixed by John Smith on 2025-03-01\nx = 1\n"
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "John Smith" not in result

    def test_detects_at_author_tag(self):
        code = '"""\n@author Tomasz Wiśniewski\n"""\ndef bar(): pass\n'
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "Tomasz" not in result

    def test_detects_copyright(self):
        code = "# Copyright 2025 Maria Garcia\ndef baz(): pass\n"
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "Maria Garcia" not in result

    def test_detects_ssn(self):
        code = '# SSN: 123-45-6789\nuser = "test"\n'
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "123-45-6789" not in result
        assert any(m.category == "SSN" for m in mappings)

    def test_detects_street_address(self):
        code = '# Office: 123 Main Street\naddr = ""\n'
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "123 Main Street" not in result

    def test_no_false_positives_on_clean_code(self):
        code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert result == code
        assert len(mappings) == 0

    def test_preserves_non_pii_comments(self):
        code = "# This function calculates the total\ndef calc(): pass\n"
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert result == code

    def test_multiple_people(self):
        code = (
            "# Author: Jan Kowalski\n"
            "# Reviewed by: Anna Nowak\n"
            "def foo(): pass\n"
        )
        anon = NLPAnonymizer()
        result, mappings = anon.anonymize(code)
        assert "Jan Kowalski" not in result
        assert "Anna Nowak" not in result
        person_mappings = [m for m in mappings if m.category == "PERSON"]
        assert len(person_mappings) == 2
