import os
import pytest
import tempfile
import fitz


@pytest.fixture
def sample_pdf():
    """Create a temporary PDF with text content for testing."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()  # close handle first so fitz can write on Windows
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Steel 50 kg, Aluminum 20 kg, Energy 100 kWh")
    doc.save(tmp.name)
    doc.close()
    yield tmp.name
    if os.path.exists(tmp.name):
        os.remove(tmp.name)


@pytest.fixture
def empty_pdf():
    """Create a temporary PDF with no text (image-only simulation)."""
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    doc = fitz.open()
    doc.new_page()
    doc.save(tmp.name)
    doc.close()
    yield tmp.name
    if os.path.exists(tmp.name):
        os.remove(tmp.name)


@pytest.fixture
def sample_analysis_result():
    """Mock AI analysis JSON response with correct CO2 calculation.

    CO2 = (50*1.89) + (20*8.24) + (100*0.499) + (500*0.062)
         = 94.5 + 164.8 + 49.9 + 31.0
         = 340.2
    """
    return {
        "project_info": {"name": "Test Project", "supplier": "Test Supplier"},
        "materials": [
            {"name": "Steel", "amount": 50, "unit": "kg", "emission_factor": 1.89, "note": "Ecoinvent"},
            {"name": "Aluminum", "amount": 20, "unit": "kg", "emission_factor": 8.24, "note": "Ecoinvent"},
        ],
        "energy": [
            {"type": "Electricity", "usage": 100, "unit": "kWh", "emission_factor": 0.499, "note": "TGO"},
        ],
        "transport": [
            {"method": "Truck", "distance": 500, "unit": "km", "emission_factor": 0.062, "note": "GLEC"},
        ],
        "total_estimated_co2": 340.20,
        "optimization_score": 65,
        "recommendations": ["Use recycled steel", "Switch to renewable energy"],
        "summary": "Test project with moderate carbon footprint",
    }
