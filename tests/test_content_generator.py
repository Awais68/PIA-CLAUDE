"""Tests for src/automations/content_generator.py — LinkedIn content generation."""

from pathlib import Path

from src.automations.content_generator import (
    TEMPLATES,
    generate_post,
    _generate_fallback,
)


class TestTemplates:
    def test_all_types_have_templates(self):
        expected = {"product_announcement", "industry_insight", "customer_success",
                    "behind_the_scenes", "general"}
        assert set(TEMPLATES.keys()) == expected

    def test_templates_are_strings(self):
        for key, template in TEMPLATES.items():
            assert isinstance(template, str)
            assert len(template) > 20


class TestGenerateFallback:
    def test_returns_string(self):
        result = _generate_fallback("New product launch", "general")
        assert isinstance(result, str)

    def test_includes_topic(self):
        result = _generate_fallback("AI Innovation", "general")
        assert "AI Innovation" in result

    def test_within_length_limit(self):
        result = _generate_fallback("x" * 2000, "general")
        assert len(result) <= 1300

    def test_includes_hashtags(self):
        result = _generate_fallback("Test topic", "general")
        assert "#" in result


class TestGeneratePost:
    def test_returns_string(self):
        result = generate_post("Our team grew 50%!")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_within_linkedin_limit(self):
        result = generate_post("Very long topic " * 100)
        assert len(result) <= 1300

    def test_works_with_context(self):
        result = generate_post("Launch", context="Q1 was great")
        assert isinstance(result, str)
