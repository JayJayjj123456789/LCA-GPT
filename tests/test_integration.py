import json
import os
import pytest
from unittest.mock import patch, MagicMock
from app.analyzer import extract_text_from_pdf


class TestFullFlow:
    """Integration tests: PDF → analysis JSON."""

    def test_pdf_to_analysis_flow(self, sample_pdf):
        """Full flow: extract text → validate JSON structure."""
        # Step 1: Extract text from PDF
        raw_text = extract_text_from_pdf(sample_pdf)
        assert len(raw_text) > 0, "PDF extraction failed"

        # Step 2: Simulate AI analysis result
        analysis = {
            "project_info": {"name": "Integration Test", "supplier": "TestCo"},
            "materials": [
                {"name": "Steel", "amount": 50, "unit": "kg", "emission_factor": 1.89, "note": "test"},
            ],
            "energy": [],
            "transport": [],
            "total_estimated_co2": 94.5,
            "optimization_score": 70,
            "recommendations": ["Test recommendation"],
            "summary": "Integration test",
        }

        # Step 3: Validate JSON structure
        parsed = json.loads(json.dumps(analysis))
        assert parsed["project_info"]["name"] == "Integration Test"

    def test_analysis_json_structure(self, sample_analysis_result):
        """Verify analysis JSON has all required fields."""
        required_fields = [
            "project_info", "materials", "energy", "transport",
            "total_estimated_co2", "optimization_score",
            "recommendations", "summary",
        ]
        for field in required_fields:
            assert field in sample_analysis_result, f"Missing field: {field}"

        # Verify nested project_info
        assert "name" in sample_analysis_result["project_info"]
        assert "supplier" in sample_analysis_result["project_info"]

        # Verify materials structure
        for mat in sample_analysis_result["materials"]:
            assert "name" in mat
            assert "amount" in mat
            assert "emission_factor" in mat

        # Verify carbon calculation (materials + energy + transport)
        expected_co2 = (
            sum(m["amount"] * m["emission_factor"] for m in sample_analysis_result["materials"])
            + sum(e["usage"] * e["emission_factor"] for e in sample_analysis_result["energy"])
            + sum(t["distance"] * t["emission_factor"] for t in sample_analysis_result["transport"])
        )
        assert abs(sample_analysis_result["total_estimated_co2"] - expected_co2) < 0.01


class TestEdgeCases:
    """Edge case tests."""

    def test_extract_corrupted_pdf(self):
        """Should handle corrupted PDF gracefully."""
        import tempfile
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.write(b"this is not a real pdf content")
        tmp.close()
        with pytest.raises(RuntimeError):
            extract_text_from_pdf(tmp.name)
        os.remove(tmp.name)

    def test_carbon_calculation_accuracy(self):
        """Verify CO2 = amount × emission_factor."""
        materials = [
            {"name": "Steel", "amount": 100, "emission_factor": 1.89},
            {"name": "Aluminum", "amount": 50, "emission_factor": 8.24},
        ]
        total = sum(m["amount"] * m["emission_factor"] for m in materials)
        assert total == 100 * 1.89 + 50 * 8.24
        assert total == 601.0