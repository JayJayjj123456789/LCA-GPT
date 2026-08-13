import os
import pytest
from unittest.mock import patch, MagicMock
from app.analyzer import extract_text_from_pdf, analyze_enterprise_carbon


class TestExtractTextFromPdf:
    """Unit tests for PDF text extraction."""

    def test_extract_valid_pdf(self, sample_pdf):
        """Should extract text from a valid PDF."""
        result = extract_text_from_pdf(sample_pdf)
        assert isinstance(result, str)
        assert len(result) > 0
        assert "Steel" in result

    def test_extract_empty_pdf(self, empty_pdf):
        """Should return empty string for PDF with no text."""
        result = extract_text_from_pdf(empty_pdf)
        assert result == ""

    def test_extract_nonexistent_file(self):
        """Should raise RuntimeError for missing file."""
        with pytest.raises(RuntimeError):
            extract_text_from_pdf("nonexistent_file.pdf")

    def test_extract_returns_string_type(self, sample_pdf):
        """Should always return a string."""
        result = extract_text_from_pdf(sample_pdf)
        assert isinstance(result, str)


class TestAnalyzeEnterpriseCarbon:
    """Unit tests for AI carbon analysis (mocked API)."""

    @patch("app.analyzer.openai.OpenAI")
    def test_analyze_returns_string(self, mock_openai):
        """Should return a JSON string from AI."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"test": "data"}'
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai.return_value = mock_client

        result = analyze_enterprise_carbon("Steel 50 kg")
        assert isinstance(result, str)
        assert "data" in result

    @patch("app.analyzer.openai.OpenAI")
    def test_analyze_empty_text(self, mock_openai):
        """Should handle empty text gracefully."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"summary": "empty"}'
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai.return_value = mock_client

        result = analyze_enterprise_carbon("")
        assert isinstance(result, str)

    @patch("app.analyzer.openai.OpenAI")
    def test_analyze_api_error_raises(self, mock_openai):
        """Should raise RuntimeError when API fails."""
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API down")
        mock_openai.return_value = mock_client

        with pytest.raises(RuntimeError):
            analyze_enterprise_carbon("Steel 50 kg")

    @patch("app.analyzer.openai.OpenAI")
    def test_analyze_long_text(self, mock_openai):
        """Should handle very long text (truncated to 8000 chars)."""
        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"summary": "long text"}'
        mock_client.chat.completions.create.return_value.choices = [mock_choice]
        mock_openai.return_value = mock_client

        long_text = "Steel 1 kg\n" * 2000
        result = analyze_enterprise_carbon(long_text)
        assert isinstance(result, str)
        # Verify the call was made (text truncated internally)
        mock_client.chat.completions.create.assert_called_once()
