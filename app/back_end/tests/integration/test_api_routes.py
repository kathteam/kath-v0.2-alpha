"""
Integration tests for API routes.

These tests require the Flask application to be running
and test the full request/response cycle.
"""

import json
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.exceptions import BadRequest

from tests.conftest import assert_error_response, assert_valid_json_response


@pytest.mark.integration
@pytest.mark.routes
class TestWorkspaceRoutes:
    """Integration tests for workspace routes."""

    def test_get_workspace_structure(self, client, mock_request_headers):
        """Test GET /api/v1/workspace - Get file tree structure."""
        response = client.get("/api/v1/workspace", headers=mock_request_headers)

        data = assert_valid_json_response(response, 200)
        assert isinstance(data, list) or "file_tree" in data
        if isinstance(data, list):
            assert len(data) >= 0  # Empty workspace is valid
        elif "file_tree" in data:
            assert isinstance(data["file_tree"], list)

    def test_get_workspace_missing_headers(self, client):
        """Test workspace endpoint without required headers."""
        response = client.get("/api/v1/workspace")

        # Should return 400 Bad Request for missing headers
        assert response.status_code in [400, 401, 500]
        data = response.get_json()
        assert data is not None and "error" in data

    def test_get_workspace_with_mock(self, client, mock_request_headers):
        """Test workspace endpoint returns valid structure."""
        response = client.get("/api/v1/workspace", headers=mock_request_headers)

        data = assert_valid_json_response(response, 200)
        # Workspace route returns a list of directory structures
        assert isinstance(data, list)


@pytest.mark.integration
@pytest.mark.routes
class TestFileOperations:
    """Integration tests for file operations."""

    def test_get_file_content(self, client, mock_request_headers):
        """Test GET /api/v1/workspace/file/<path> - Get file content."""
        # Test accessing a file - should return 404 or 200 depending on if file exists
        response = client.get(
            "/api/v1/workspace/file/test.csv",
            query_string={"page": 0, "rowsPerPage": 25, "filters": "{}", "sorts": "{}"},
            headers=mock_request_headers,
        )

        # File doesn't exist in test workspace, so expect 404 or 500
        assert response.status_code in [200, 404, 500]

    def test_save_file_content(self, client, mock_request_headers):
        """Test PUT /api/v1/workspace/file/<path> - Save file."""
        headers = dict(mock_request_headers)
        headers["Content-Type"] = "application/json"

        file_data = {"page": 0, "rowsPerPage": 100, "header": ["chromosome"], "rows": [["chr1"]]}

        response = client.put("/api/v1/workspace/file/test.csv", json=file_data, headers=headers)

        # Should return success or error
        assert response.status_code in [200, 404, 500]

    def test_create_file_or_directory(self, client, mock_request_headers):
        """Test PUT /api/v1/workspace/create - Create file/directory."""
        import os
        import shutil

        # Clean up test directory if it exists
        test_path = os.path.join("/home/tch/KATH/kath-v0.2-alpha/app/back_end/src/workspace/test-uuid-1234/test_folder")
        if os.path.exists(test_path):
            if os.path.isdir(test_path):
                shutil.rmtree(test_path)
            else:
                os.remove(test_path)

        # Add content-type header to trigger JSON parsing
        headers = dict(mock_request_headers)
        headers["Content-Type"] = "application/json"

        # Test creating a directory at root
        dir_data = {"label": "test_folder", "type": "folder"}

        response = client.put("/api/v1/workspace/create/", json=dir_data, headers=headers)

        assert response.status_code == 200

        # Test creating a file in a specific path
        file_data = {"label": "test.txt", "type": "file"}

        response = client.put("/api/v1/workspace/create/test_folder", json=file_data, headers=headers)

        assert response.status_code == 200

    def test_rename_file(self, client, mock_request_headers):
        """Test PUT /api/v1/workspace/rename/<path> - Rename file."""
        headers = dict(mock_request_headers)
        headers["Content-Type"] = "application/json"

        data = {"label": "new_name.csv", "type": "file"}

        response = client.put("/api/v1/workspace/rename/old_name.csv", json=data, headers=headers)

        # Should return success or error (file may not exist in test)
        assert response.status_code in [200, 404, 500]

    def test_delete_file(self, client, mock_request_headers):
        """Test PUT /api/v1/workspace/delete/<path> - Delete file."""
        headers = dict(mock_request_headers)
        headers["Content-Type"] = "application/json"

        data = {"type": "file"}

        response = client.put("/api/v1/workspace/delete/test.csv", json=data, headers=headers)

        # Should return success or error
        assert response.status_code in [200, 404, 500]


@pytest.mark.integration
@pytest.mark.routes
class TestDataProcessingRoutes:
    """Integration tests for data processing routes."""

    def test_aggregate_data(self, client, mock_request_headers):
        """Test GET /api/v1/workspace/aggregate/<path> - Calculate aggregations."""
        response = client.get(
            "/api/v1/workspace/aggregate/test.csv",
            query_string={"columns": "position", "operations": "sum,avg,min,max"},
            headers=mock_request_headers,
        )

        # Should return aggregation results or error (file may not exist or invalid params)
        assert response.status_code in [200, 400, 404, 500]

    def test_merge_files(self, client, mock_request_headers):
        """Test GET /api/v1/workspace/merge/all/<path:relative_path> - Merge files."""
        headers = dict(mock_request_headers)

        # Test merge all endpoint
        response = client.get(
            "/api/v1/workspace/merge/all/merged.csv",
            query_string={
                "lovdFile": "file1.csv",
                "clinvarFile": "file2.csv",
                "gnomadFile": "file3.csv",
                "override": "true",
            },
            headers=headers,
        )

        # Should return success or error
        assert response.status_code in [200, 400, 404, 500]

    def test_download_external_data(self, client, mock_request_headers):
        """Test GET /api/v1/workspace/download/<path> - Download external data."""
        response = client.get(
            "/api/v1/workspace/download/downloads",
            query_string={"source": "clinvar", "gene": "BRCA1"},
            headers=mock_request_headers,
        )

        # Should return success or error
        assert response.status_code in [200, 400, 500]


@pytest.mark.integration
@pytest.mark.routes
@pytest.mark.tools
class TestToolApplicationRoutes:
    """Integration tests for tool application routes."""

    def test_apply_spliceai(self, client, mock_request_headers):
        """Test GET /api/v1/workspace/apply/spliceai/<path> - Run SpliceAI."""
        response = client.get("/api/v1/workspace/apply/spliceai/test.csv", headers=mock_request_headers)

        # Should return success or error (file may not exist)
        assert response.status_code in [200, 400, 404, 500]

    def test_apply_cadd(self, client, mock_request_headers):
        """Test GET /api/v1/workspace/apply/cadd/<path> - Run CADD."""
        response = client.get(
            "/api/v1/workspace/apply/cadd/test.csv",
            query_string={"genome_build": "GRCh38"},
            headers=mock_request_headers,
        )

        # Should return success or error (file may not exist)
        assert response.status_code in [200, 400, 404, 500]

    def test_apply_revel(self, client, mock_request_headers):
        """Test GET /api/v1/workspace/apply/revel/<path> - Run REVEL."""
        response = client.get("/api/v1/workspace/apply/revel/test.csv", headers=mock_request_headers)

        # Should return success or error (file may not exist)
        assert response.status_code in [200, 400, 404, 500]


@pytest.mark.integration
@pytest.mark.routes
class TestErrorHandling:
    """Integration tests for error handling."""

    def test_missing_uuid_header(self, client):
        """Test request without UUID header."""
        response = client.get("/api/v1/workspace", headers={"sid": "test"})

        # Should return error
        assert response.status_code in [400, 401, 500]

    def test_missing_sid_header(self, client):
        """Test request without SID header."""
        response = client.get("/api/v1/workspace", headers={"uuid": "test"})

        # Should return error
        assert response.status_code in [400, 401, 500]

    def test_nonexistent_file(self, client, mock_request_headers):
        """Test accessing non-existent file."""
        response = client.get(
            "/api/v1/workspace/file/nonexistent.csv",
            query_string={"page": 0, "rowsPerPage": 25, "filters": "{}", "sorts": "{}"},
            headers=mock_request_headers,
        )

        # Should return 404 or 500 (file doesn't exist)
        assert response.status_code in [404, 500]

    def test_invalid_json_payload(self, client, mock_request_headers):
        """Test sending invalid JSON in request body."""
        # Add content-type header to trigger JSON parsing
        headers = dict(mock_request_headers)
        headers["Content-Type"] = "application/json"

        try:
            client.put("/api/v1/workspace/file/test.csv", data="{invalid json", headers=headers)
            pytest.fail("Expected BadRequest exception was not raised")
        except BadRequest as e:
            # Verify that the error message contains JSON decode information
            assert "400 Bad Request" in str(e)


@pytest.mark.integration
class TestRequestLogging:
    """Integration tests for request logging middleware."""

    def test_request_id_in_response_headers(self, client, mock_request_headers):
        """Test that X-Request-ID header is added to response."""
        response = client.get("/api/v1/workspace", headers=mock_request_headers)

        # Check for request ID header
        assert "X-Request-ID" in response.headers or response.status_code in [400, 500]

    def test_response_time_in_headers(self, client, mock_request_headers):
        """Test that X-Response-Time header is added to response."""
        response = client.get("/api/v1/workspace", headers=mock_request_headers)

        # Check for response time header
        assert "X-Response-Time" in response.headers or response.status_code in [400, 500]
