import pytest
from unittest.mock import MagicMock, patch
from app.database import get_driver, reset_neo4j_data, ingest_analysis_to_graph


class TestGetDriver:
    """Unit tests for Neo4j driver creation."""

    @patch("app.database.GraphDatabase")
    def test_get_driver_returns_driver(self, mock_graph_db):
        """Should return a driver instance."""
        mock_driver = MagicMock()
        mock_graph_db.driver.return_value = mock_driver
        driver = get_driver()
        assert driver == mock_driver
        mock_graph_db.driver.assert_called_once()


class TestResetNeo4jData:
    """Unit tests for database reset."""

    @patch("app.database.get_driver")
    def test_reset_success(self, mock_get_driver):
        """Should return True on successful reset."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        result = reset_neo4j_data()
        assert result is True
        mock_driver.close.assert_called_once()

    @patch("app.database.get_driver")
    def test_reset_failure_raises(self, mock_get_driver):
        """Should raise RuntimeError on failure."""
        mock_driver = MagicMock()
        mock_driver.session.side_effect = Exception("Connection refused")
        mock_get_driver.return_value = mock_driver
        with pytest.raises(RuntimeError):
            reset_neo4j_data()
        mock_driver.close.assert_called_once()


class TestIngestAnalysisToGraph:
    """Unit tests for data ingestion."""

    @patch("app.database.get_driver")
    def test_ingest_valid_data(self, mock_get_driver, sample_analysis_result):
        """Should ingest valid analysis data without error."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        ingest_analysis_to_graph(sample_analysis_result)
        mock_driver.close.assert_called_once()

    @patch("app.database.get_driver")
    def test_ingest_empty_materials(self, mock_get_driver):
        """Should handle data with empty materials list."""
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        data = {
            "project_info": {"name": "Empty", "supplier": "None"},
            "materials": [],
            "energy": [],
            "transport": [],
            "total_estimated_co2": 0,
            "optimization_score": 0,
            "recommendations": [],
            "summary": "Empty project",
        }
        ingest_analysis_to_graph(data)
        mock_driver.close.assert_called_once()

    @patch("app.database.get_driver")
    def test_ingest_failure_raises(self, mock_get_driver, sample_analysis_result):
        """Should raise error when Neo4j is unreachable."""
        mock_driver = MagicMock()
        mock_driver.session.side_effect = Exception("DB offline")
        mock_get_driver.return_value = mock_driver
        with pytest.raises(Exception):
            ingest_analysis_to_graph(sample_analysis_result)
        mock_driver.close.assert_called_once()
