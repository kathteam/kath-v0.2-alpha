"""
API Endpoint Tests for Phase 2

Comprehensive tests for all Phase 2 REST API endpoints.
"""

import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.routes.workspace_phase2_route import workspace_phase2_route_bp


@pytest.fixture
def client(app):
    """Get Flask test client."""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Get standard auth headers."""
    return {
        "uuid": "test-uuid-12345",
        "sid": "test-session-67890",
        "Content-Type": "application/json"
    }


class TestDeltaSyncEndpoints:
    """Tests for delta-sync API endpoints."""

    def test_delta_sync_status_endpoint_exists(self, client):
        """Test delta-sync status endpoint is accessible."""
        response = client.get(
            "/workspace_phase2/delta-sync/status/test-file.csv",
            headers={"uuid": "test", "source": "clinvar"}
        )
        # Should not be 404
        assert response.status_code != 404

    def test_delta_sync_status_requires_uuid(self, client):
        """Test delta-sync status endpoint requires UUID."""
        response = client.get(
            "/workspace_phase2/delta-sync/status/test-file.csv",
            headers={"source": "clinvar"}  # No UUID
        )
        # Should require UUID header
        assert response.status_code == 400

    def test_delta_sync_status_requires_source(self, client):
        """Test delta-sync status endpoint requires source parameter."""
        response = client.get(
            "/workspace_phase2/delta-sync/status/test-file.csv",
            headers={"uuid": "test"}
            # No source parameter
        )
        # Should require source
        assert response.status_code == 400

    def test_delta_sync_statistics_endpoint_exists(self, client):
        """Test delta-sync statistics endpoint is accessible."""
        response = client.get(
            "/workspace_phase2/delta-sync/statistics/test-workspace"
        )
        # Should not be 404
        assert response.status_code != 404


class TestMergeEndpoints:
    """Tests for merge API endpoints."""

    def test_merge_strategies_endpoint(self, client):
        """Test merge strategies endpoint."""
        response = client.get("/workspace_phase2/merge/strategies")

        assert response.status_code == 200
        data = response.get_json()
        assert "strategies" in data
        assert isinstance(data["strategies"], list)
        assert len(data["strategies"]) > 0

    def test_merge_strategies_have_descriptions(self, client):
        """Test merge strategies include descriptions."""
        response = client.get("/workspace_phase2/merge/strategies")
        data = response.get_json()

        for strategy in data["strategies"]:
            assert "name" in strategy
            assert "description" in strategy

    def test_merge_perform_endpoint_requires_auth(self, client):
        """Test merge perform endpoint requires authentication."""
        response = client.post(
            "/workspace_phase2/merge/perform",
            json={"file_id": 1, "sources": ["clinvar"], "strategy": "outer_union"}
            # No auth headers
        )
        # Should require auth headers
        assert response.status_code == 400

    def test_merge_perform_endpoint_requires_file_id(self, client, auth_headers):
        """Test merge perform endpoint requires file_id."""
        response = client.post(
            "/workspace_phase2/merge/perform",
            json={"sources": ["clinvar"], "strategy": "outer_union"},
            headers=auth_headers
        )
        # Should require file_id
        assert response.status_code == 400

    def test_merge_perform_endpoint_requires_sources(self, client, auth_headers):
        """Test merge perform endpoint requires sources."""
        response = client.post(
            "/workspace_phase2/merge/perform",
            json={"file_id": 1, "strategy": "outer_union"},
            headers=auth_headers
        )
        # Should require sources
        assert response.status_code == 400

    def test_merge_history_endpoint(self, client):
        """Test merge history endpoint."""
        response = client.get("/workspace_phase2/merge/history/1")

        assert response.status_code in [200, 404]  # May return 404 if file doesn't exist
        if response.status_code == 200:
            data = response.get_json()
            assert "data" in data

    def test_merge_statistics_endpoint(self, client):
        """Test merge statistics endpoint."""
        response = client.get("/workspace_phase2/merge/statistics/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "data" in data


class TestFilteringEndpoints:
    """Tests for filtering API endpoints."""

    def test_filter_apply_endpoint_requires_auth(self, client):
        """Test filter apply endpoint requires authentication."""
        response = client.post(
            "/workspace_phase2/filter/apply",
            json={"file_id": 1}
            # No auth headers
        )
        # Should require auth
        assert response.status_code == 400

    def test_filter_apply_endpoint_requires_file_id(self, client, auth_headers):
        """Test filter apply endpoint requires file_id."""
        response = client.post(
            "/workspace_phase2/filter/apply",
            json={},  # No file_id
            headers=auth_headers
        )
        # Should require file_id
        assert response.status_code == 400

    def test_quality_summary_endpoint(self, client):
        """Test quality summary endpoint."""
        response = client.get("/workspace_phase2/filter/quality-summary/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "data" in data

    def test_filtering_history_endpoint(self, client):
        """Test filtering history endpoint."""
        response = client.get("/workspace_phase2/filter/history/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "data" in data


class TestAnalysisEndpoints:
    """Tests for analysis API endpoints."""

    def test_analysis_tools_endpoint(self, client):
        """Test analysis tools endpoint."""
        response = client.get("/workspace_phase2/analysis/tools")

        assert response.status_code == 200
        data = response.get_json()
        assert "tools" in data
        assert "status" in data

    def test_analysis_tools_include_cadd(self, client):
        """Test CADD tool is in response."""
        response = client.get("/workspace_phase2/analysis/tools")
        data = response.get_json()

        assert "cadd" in data["tools"]
        cadd_info = data["tools"]["cadd"]
        assert "score_range" in cadd_info
        assert "pathogenicity_threshold" in cadd_info

    def test_analysis_tools_include_revel(self, client):
        """Test REVEL tool is in response."""
        response = client.get("/workspace_phase2/analysis/tools")
        data = response.get_json()

        assert "revel" in data["tools"]
        revel_info = data["tools"]["revel"]
        assert "score_range" in revel_info
        assert "pathogenicity_threshold" in revel_info

    def test_analysis_tools_include_spliceai(self, client):
        """Test SpliceAI tool is in response."""
        response = client.get("/workspace_phase2/analysis/tools")
        data = response.get_json()

        assert "spliceai" in data["tools"]
        spliceai_info = data["tools"]["spliceai"]
        assert "score_range" in spliceai_info
        assert "pathogenicity_threshold" in spliceai_info

    def test_variant_scores_endpoint(self, client):
        """Test variant scores endpoint."""
        response = client.get("/workspace_phase2/analysis/variant-scores/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "scores" in data
            assert "variant_id" in data

    def test_pathogenic_variants_endpoint(self, client):
        """Test pathogenic variants endpoint."""
        response = client.get("/workspace_phase2/analysis/pathogenic/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "count" in data
            assert "variants" in data

    def test_analysis_statistics_endpoint(self, client):
        """Test analysis statistics endpoint."""
        response = client.get("/workspace_phase2/analysis/statistics/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "data" in data


class TestDataQueryEndpoints:
    """Tests for data query API endpoints."""

    def test_source_variants_endpoint(self, client):
        """Test source variants endpoint."""
        response = client.get("/workspace_phase2/variants/source/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "count" in data
            assert "data" in data

    def test_source_variants_with_pagination(self, client):
        """Test source variants endpoint with pagination."""
        response = client.get(
            "/workspace_phase2/variants/source/1?limit=50&offset=0"
        )

        assert response.status_code in [200, 404]

    def test_merged_variants_endpoint(self, client):
        """Test merged variants endpoint."""
        response = client.get("/workspace_phase2/variants/merged/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "count" in data
            assert "data" in data

    def test_merged_variants_with_gene_filter(self, client):
        """Test merged variants endpoint with gene filter."""
        response = client.get(
            "/workspace_phase2/variants/merged/1?gene=BRCA2"
        )

        assert response.status_code in [200, 404]

    def test_filtered_variants_endpoint(self, client):
        """Test filtered variants endpoint."""
        response = client.get("/workspace_phase2/variants/filtered/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "count" in data
            assert "data" in data

    def test_filtered_variants_with_validity_filter(self, client):
        """Test filtered variants endpoint with validity filter."""
        response = client.get(
            "/workspace_phase2/variants/filtered/1?valid_only=true"
        )

        assert response.status_code in [200, 404]


class TestAuditTrailEndpoints:
    """Tests for audit trail API endpoints."""

    def test_audit_file_endpoint(self, client):
        """Test file audit trail endpoint."""
        response = client.get("/workspace_phase2/audit/file/1")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "count" in data
            assert "data" in data

    def test_audit_operation_endpoint(self, client):
        """Test operation audit endpoint."""
        response = client.get("/workspace_phase2/audit/operation/1/merge")

        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.get_json()
            assert "operation" in data
            assert "count" in data
            assert "data" in data


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/workspace_phase2/health")

        assert response.status_code == 200
        data = response.get_json()
        assert "status" in data
        assert "version" in data
        assert "components" in data

    def test_health_endpoint_components(self, client):
        """Test health endpoint includes all components."""
        response = client.get("/workspace_phase2/health")
        data = response.get_json()

        components = data["components"]
        assert "delta_sync" in components
        assert "merge" in components
        assert "filtering" in components
        assert "analysis" in components


class TestAPIResponseFormats:
    """Tests for API response formats."""

    def test_success_response_format(self, client):
        """Test successful API responses have correct format."""
        response = client.get("/workspace_phase2/analysis/tools")

        data = response.get_json()
        # Should have status field
        assert "status" in data
        assert data["status"] == "success"

    def test_error_response_format(self, client):
        """Test error API responses have correct format."""
        response = client.post(
            "/workspace_phase2/merge/perform",
            json={"file_id": 1},  # Missing required fields
            headers={"uuid": "test", "sid": "test"}
        )

        if response.status_code == 400:
            data = response.get_json()
            # Should have error field
            assert "error" in data or "message" in data

    def test_json_content_type(self, client):
        """Test all endpoints return JSON content type."""
        endpoints = [
            "/workspace_phase2/merge/strategies",
            "/workspace_phase2/analysis/tools",
            "/workspace_phase2/health",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.content_type == "application/json"


class TestAPIErrorHandling:
    """Tests for API error handling."""

    def test_missing_required_headers(self, client):
        """Test endpoints requiring headers return 400 when missing."""
        response = client.post(
            "/workspace_phase2/merge/perform",
            json={"file_id": 1, "sources": ["clinvar"]}
            # Missing uuid and sid
        )

        assert response.status_code == 400

    def test_invalid_json_body(self, client):
        """Test endpoints handle invalid JSON gracefully."""
        response = client.post(
            "/workspace_phase2/merge/perform",
            data="invalid json",
            headers={"uuid": "test", "sid": "test"}
        )

        assert response.status_code in [400, 415]

    def test_not_found_handling(self, client):
        """Test 404 handling for non-existent resources."""
        response = client.get(
            "/workspace_phase2/variants/source/99999"
        )

        # Should return 404 or empty data, not 500
        assert response.status_code != 500

    def test_internal_error_handling(self, client):
        """Test 500 error handling."""
        # This would need specific conditions to trigger
        # For now, just ensure endpoints don't crash
        endpoints = [
            "/workspace_phase2/analysis/tools",
            "/workspace_phase2/merge/strategies",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code != 500


class TestAPIIntegration:
    """Integration tests for API workflows."""

    def test_merge_workflow_via_api(self, client, auth_headers):
        """Test merge workflow through API."""
        # 1. Get available strategies
        strategies_resp = client.get("/workspace_phase2/merge/strategies")
        assert strategies_resp.status_code == 200
        strategies = strategies_resp.get_json()["strategies"]
        assert len(strategies) > 0

        # 2. Attempt merge (may fail due to no data, but endpoint should work)
        merge_resp = client.post(
            "/workspace_phase2/merge/perform",
            json={
                "file_id": 1,
                "sources": ["clinvar"],
                "strategy": strategies[0]["name"]
            },
            headers=auth_headers
        )

        # Should be 4xx (missing data) or 200, not 500
        assert merge_resp.status_code != 500

    def test_analysis_workflow_via_api(self, client):
        """Test analysis workflow through API."""
        # 1. Get analysis tools
        tools_resp = client.get("/workspace_phase2/analysis/tools")
        assert tools_resp.status_code == 200
        tools = tools_resp.get_json()["tools"]
        assert len(tools) > 0

        # 2. Check pathogenic variants
        pathogenic_resp = client.get(
            "/workspace_phase2/analysis/pathogenic/1"
        )

        # Should work or return 404, not 500
        assert pathogenic_resp.status_code != 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
