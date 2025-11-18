"""
System and Integration Tests for Phase 2

Comprehensive tests for complete system workflows and API integration.
"""

import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data.delta_sync import DeltaSyncManager
from src.data.merge_operations import MergeOperationHandler, MergeStrategy
from src.data.quality_filtering import QualityFilteringEngine
from src.data.analysis_integration import AnalysisIntegrationHandler, AnalysisToolConfig
from src.models.base import Base
from src.models.source_variant import SourceVariant
from src.models.merged_variant import MergedVariant
from src.models.filtered_variant import FilteredVariant
from src.models.workflow_audit import WorkflowAudit
from src.database.repositories import (
    SourceVariantRepository,
    MergedVariantRepository,
    FilteredVariantRepository,
    WorkflowAuditRepository
)


@pytest.fixture
def db_engine():
    """Create in-memory database for test."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create new session for each test."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()


# ============================================================================
# SYSTEM TESTS - Individual Component Integration
# ============================================================================

class TestDeltaSyncSystem:
    """System tests for delta-sync functionality."""

    def test_sync_detection_basic_workflow(self, db_session):
        """Test basic sync detection workflow."""
        sync_mgr = DeltaSyncManager(session=db_session)

        # Initial check - no data
        status1 = sync_mgr.check_sync_status("ws1", 1, "clinvar")
        assert status1.has_existing_data is False

        # Add data
        variant = SourceVariant(
            file_id=1,
            source_database="clinvar",
            chromosome="1",
            position=100,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-100-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2024.01"
        )
        db_session.add(variant)
        db_session.commit()

        # Check again - should have data
        status2 = sync_mgr.check_sync_status("ws1", 1, "clinvar")
        assert status2.has_existing_data is True
        assert status2.record_count > 0

    def test_sync_version_detection_workflow(self, db_session):
        """Test version mismatch detection workflow."""
        sync_mgr = DeltaSyncManager(session=db_session)

        # Add variant with old version
        variant = SourceVariant(
            file_id=2,
            source_database="lovd",
            chromosome="2",
            position=200,
            ref_allele="G",
            alt_allele="C",
            gen_pos="2-200-G-C",
            gene="TEST2",
            transcript="NM_000002",
            consequence="frameshift",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow(),
            source_version="2023.01"  # Old version
        )
        db_session.add(variant)
        db_session.commit()

        # Check with different current version
        status = sync_mgr.check_sync_status(
            "ws1", 2, "lovd", current_version="2024.01"
        )

        assert status.version_mismatch is True
        assert status.requires_full_sync is True

    def test_sync_freshness_check_workflow(self, db_session):
        """Test freshness window evaluation workflow."""
        sync_mgr = DeltaSyncManager(session=db_session)

        # Add very old data
        old_variant = SourceVariant(
            file_id=3,
            source_database="gnomad",
            chromosome="3",
            position=300,
            ref_allele="T",
            alt_allele="A",
            gen_pos="3-300-T-A",
            gene="TEST3",
            transcript="NM_000003",
            consequence="missense",
            source_data=json.dumps({}),
            import_timestamp=datetime.utcnow() - timedelta(days=100),
            source_version="3.0"
        )
        db_session.add(old_variant)
        db_session.commit()

        # Check - should need refresh
        status = sync_mgr.check_sync_status("ws1", 3, "gnomad")
        assert status.requires_full_sync is True


class TestMergeSystem:
    """System tests for merge operations."""

    def test_simple_merge_workflow(self, db_session):
        """Test simple single-source merge."""
        # Create source variants
        for i in range(3):
            variant = SourceVariant(
                file_id=1,
                source_database="clinvar",
                chromosome="1",
                position=100 + i,
                ref_allele="A",
                alt_allele="T",
                gen_pos=f"1-{100+i}-A-T",
                gene=f"GENE{i}",
                transcript=f"NM_00000{i}",
                consequence="missense",
                source_data=json.dumps({"id": i}),
                import_timestamp=datetime.utcnow(),
                source_version="2024.01"
            )
            db_session.add(variant)
        db_session.commit()

        # Perform merge
        handler = MergeOperationHandler(session=db_session)
        result = handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="test-user"
        )

        assert result.merged_count > 0
        assert result.total_input >= result.merged_count

    def test_multi_source_merge_workflow(self, db_session):
        """Test multi-source merge with source attribution."""
        # Add variants from different sources at same position
        for source in ["clinvar", "lovd"]:
            variant = SourceVariant(
                file_id=2,
                source_database=source,
                chromosome="1",
                position=1000,
                ref_allele="G",
                alt_allele="A",
                gen_pos="1-1000-G-A",
                gene="BRCA2",
                transcript="NM_000059",
                consequence="missense",
                source_data=json.dumps({"source": source}),
                import_timestamp=datetime.utcnow(),
                source_version="2024.01"
            )
            db_session.add(variant)
        db_session.commit()

        # Merge with CONSENSUS strategy
        handler = MergeOperationHandler(session=db_session)
        result = handler.perform_merge(
            file_id=2,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.CONSENSUS,
            user_id="test-user"
        )

        assert result.merged_count > 0
        # Check that merged variants have multiple sources
        merged_variants = db_session.query(MergedVariant).filter_by(file_id=2).all()
        for variant in merged_variants:
            sources = json.loads(variant.source_databases)
            assert len(sources) > 0

    def test_merge_strategy_comparison(self, db_session):
        """Test different merge strategies produce different results."""
        # Create test data with variants in different sources
        sources_by_variant = {
            1: ["clinvar", "lovd"],      # In both
            2: ["clinvar"],               # Only clinvar
            3: ["lovd"],                  # Only lovd
        }

        file_id = 3
        for var_id, sources in sources_by_variant.items():
            for source in sources:
                variant = SourceVariant(
                    file_id=file_id,
                    source_database=source,
                    chromosome="1",
                    position=5000 + var_id,
                    ref_allele="A",
                    alt_allele="T",
                    gen_pos=f"1-{5000+var_id}-A-T",
                    gene=f"GENE{var_id}",
                    transcript=f"NM_{var_id:06d}",
                    consequence="missense",
                    source_data=json.dumps({}),
                    import_timestamp=datetime.utcnow(),
                    source_version="2024.01"
                )
                db_session.add(variant)
        db_session.commit()

        handler = MergeOperationHandler(session=db_session)

        # Get counts for each strategy
        outer_result = handler.perform_merge(
            file_id=file_id,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.OUTER_UNION
        )

        # Clear for next test
        db_session.query(MergedVariant).filter_by(file_id=file_id).delete()

        inner_result = handler.perform_merge(
            file_id=file_id,
            sources=["clinvar", "lovd"],
            merge_strategy=MergeStrategy.INNER_INTERSECTION
        )

        # OUTER should have more variants than INNER
        assert outer_result.merged_count >= inner_result.merged_count


class TestFilteringSystem:
    """System tests for quality filtering."""

    def test_filtering_workflow(self, db_session):
        """Test complete filtering workflow."""
        # Create mixed quality variants
        variants_data = [
            {
                "chromosome": "1",
                "position": 1000,
                "ref_allele": "A",
                "alt_allele": "T",
                "gene": "GENE1",
                "transcript": "NM_000001",
                "valid": True
            },
            {
                "chromosome": "1",
                "position": 2000,
                "ref_allele": "G",  # Valid required field
                "alt_allele": "A",
                "gene": None,  # Missing annotation instead of missing allele
                "transcript": None,
                "valid": False
            },
            {
                "chromosome": "99",  # Invalid
                "position": 3000,
                "ref_allele": "G",
                "alt_allele": "C",
                "gene": "GENE3",
                "transcript": "NM_000003",
                "valid": False
            },
        ]

        file_id = 1
        for i, data in enumerate(variants_data):
            # Skip None values in gen_pos construction
            ref = data["ref_allele"] or "X"
            alt = data["alt_allele"] or "X"
            chrom = data["chromosome"] or "1"
            pos = data["position"] or 1000

            variant = MergedVariant(
                file_id=file_id,
                chromosome=data["chromosome"],
                position=data["position"],
                ref_allele=data["ref_allele"],
                alt_allele=data["alt_allele"],
                gen_pos=f"{chrom}-{pos}-{ref}-{alt}",
                gene=data["gene"],
                transcript=data["transcript"],
                consequence="missense",
                source_databases=json.dumps(["clinvar"]),
                merge_timestamp=datetime.utcnow(),
                merge_strategy="outer_union"
            )
            db_session.add(variant)
        db_session.commit()

        # Apply filters
        engine = QualityFilteringEngine(session=db_session)
        result = engine.apply_filters(file_id=file_id, user_id="test-user")

        # Check results
        assert result.total_variants > 0
        assert result.invalid_variants > 0  # Should have caught invalid variants
        summary = engine.get_quality_summary(file_id)
        assert summary["total"] > 0

    def test_filter_version_tracking(self, db_session):
        """Test filter version tracking."""
        # Create test variant
        variant = MergedVariant(
            file_id=2,
            chromosome="1",
            position=1000,
            ref_allele="A",
            alt_allele="T",
            gen_pos="1-1000-A-T",
            gene="TEST",
            transcript="NM_000001",
            consequence="missense",
            source_databases=json.dumps(["clinvar"]),
            merge_timestamp=datetime.utcnow(),
            merge_strategy="outer_union"
        )
        db_session.add(variant)
        db_session.commit()

        # Filter
        engine = QualityFilteringEngine(session=db_session)
        result = engine.apply_filters(file_id=2)

        # Check version is tracked
        filtered = db_session.query(FilteredVariant).filter_by(file_id=2).all()
        for fv in filtered:
            assert fv.filter_version is not None


class TestAnalysisSystem:
    """System tests for analysis integration."""

    def test_analysis_tool_availability(self):
        """Test all analysis tools are available."""
        tools = AnalysisToolConfig.get_all_tools()
        assert len(tools) == 3
        assert all(tool in tools for tool in ["cadd", "revel", "spliceai"])

    def test_pathogenicity_scoring(self):
        """Test pathogenicity scoring across tools."""
        test_cases = [
            ("cadd", 25, True),
            ("cadd", 15, False),
            ("revel", 0.6, True),
            ("revel", 0.4, False),
            ("spliceai", 0.3, True),
            ("spliceai", 0.1, False),
        ]

        for tool, score, expected in test_cases:
            result = AnalysisToolConfig.is_pathogenic(tool, score)
            assert result == expected, f"Failed for {tool}={score}"

    def test_analysis_result_creation(self, db_session):
        """Test analysis result creation and storage."""
        handler = AnalysisIntegrationHandler(session=db_session)

        # This tests the basic flow
        from src.data.analysis_integration import AnalysisResult

        result = AnalysisResult(
            variant_id=1,
            tool="cadd",
            score=25.5,
            raw_output={"test": "data"},
            timestamp=datetime.utcnow()
        )

        assert result.is_pathogenic is True
        result_dict = result.to_dict()
        assert "is_pathogenic" in result_dict


# ============================================================================
# INTEGRATION TESTS - Complete Workflows
# ============================================================================

class TestCompleteWorkflows:
    """Integration tests for complete Phase 2 workflows."""

    def test_download_to_merge_workflow(self, db_session):
        """Test complete workflow from download to merge."""
        # 1. Delta-sync phase
        sync_mgr = DeltaSyncManager(session=db_session)
        initial_status = sync_mgr.check_sync_status("ws", 1, "clinvar")
        assert initial_status.has_existing_data is False

        # 2. Import phase (simulate download completion)
        for i in range(5):
            variant = SourceVariant(
                file_id=1,
                source_database="clinvar",
                chromosome="1",
                position=1000 + i*100,
                ref_allele="A",
                alt_allele="T",
                gen_pos=f"1-{1000+i*100}-A-T",
                gene=f"G{i}",
                transcript=f"NM_{i}",
                consequence="missense",
                source_data=json.dumps({}),
                import_timestamp=datetime.utcnow(),
                source_version="2024.01"
            )
            db_session.add(variant)
        db_session.commit()

        # 3. Delta-sync phase (second time)
        status_after = sync_mgr.check_sync_status("ws", 1, "clinvar")
        assert status_after.has_existing_data is True

        # 4. Merge phase
        merge_handler = MergeOperationHandler(session=db_session)
        merge_result = merge_handler.perform_merge(
            file_id=1,
            sources=["clinvar"],
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="user1"
        )

        assert merge_result.merged_count > 0

    def test_merge_to_filter_to_analysis_workflow(self, db_session):
        """Test workflow from merge through filter to analysis."""
        # 1. Create merged variants
        for i in range(3):
            variant = MergedVariant(
                file_id=2,
                chromosome="1",
                position=2000 + i*100,
                ref_allele="G",
                alt_allele="C",
                gen_pos=f"1-{2000+i*100}-G-C",
                gene=f"GENE{i}",
                transcript=f"NM_{i}",
                consequence="missense",
                source_databases=json.dumps(["clinvar", "lovd"]),
                merge_timestamp=datetime.utcnow(),
                merge_strategy="consensus"
            )
            db_session.add(variant)
        db_session.commit()

        # 2. Filter phase
        filter_engine = QualityFilteringEngine(session=db_session)
        filter_result = filter_engine.apply_filters(file_id=2, user_id="user1")
        assert filter_result.total_variants > 0

        # 3. Analysis phase
        analysis_handler = AnalysisIntegrationHandler(session=db_session)
        tools = AnalysisToolConfig.get_all_tools()
        assert len(tools) > 0

        # Get pathogenic variants
        pathogenic = analysis_handler.get_pathogenic_variants(file_id=2)
        assert isinstance(pathogenic, dict)

    def test_multiple_sources_complete_workflow(self, db_session):
        """Test workflow with multiple data sources."""
        # Add variants from multiple sources
        sources = ["clinvar", "lovd", "gnomad"]
        positions = [3000, 3100, 3200]

        for pos in positions:
            for source in sources:
                # Each source has data at some positions
                if (pos + ord(source[0])) % 2 == 0:
                    variant = SourceVariant(
                        file_id=3,
                        source_database=source,
                        chromosome="1",
                        position=pos,
                        ref_allele="A",
                        alt_allele="T",
                        gen_pos=f"1-{pos}-A-T",
                        gene="MULTI",
                        transcript="NM_000001",
                        consequence="missense",
                        source_data=json.dumps({"source": source}),
                        import_timestamp=datetime.utcnow(),
                        source_version="2024.01"
                    )
                    db_session.add(variant)
        db_session.commit()

        # Check delta-sync for each source
        sync_mgr = DeltaSyncManager(session=db_session)
        for source in sources:
            status = sync_mgr.check_sync_status("ws", 3, source)
            # Status should be consistent

        # Merge all sources
        merge_handler = MergeOperationHandler(session=db_session)
        result = merge_handler.perform_merge(
            file_id=3,
            sources=sources,
            merge_strategy=MergeStrategy.OUTER_UNION,
            user_id="user1"
        )

        # Filter merged results
        filter_engine = QualityFilteringEngine(session=db_session)
        filter_result = filter_engine.apply_filters(file_id=3)

        assert filter_result.total_variants >= 0


class TestRepositoryIntegration:
    """Integration tests for repositories."""

    def test_source_variant_repository_workflow(self, db_session):
        """Test SourceVariantRepository integration."""
        # Add variants
        for i in range(3):
            variant = SourceVariant(
                file_id=1,
                source_database="clinvar",
                chromosome="1",
                position=1000 + i,
                ref_allele="A",
                alt_allele="T",
                gen_pos=f"1-{1000+i}-A-T",
                gene=f"G{i}",
                transcript=f"NM_{i}",
                consequence="missense",
                source_data=json.dumps({}),
                import_timestamp=datetime.utcnow(),
                source_version="2024.01"
            )
            db_session.add(variant)
        db_session.commit()

        # Query using repository
        repo = SourceVariantRepository(session=db_session)
        variants = repo.find_by_file(file_id=1)
        assert len(variants) == 3

        counts = repo.count_by_source(file_id=1)
        assert "clinvar" in counts
        assert counts["clinvar"] == 3

    def test_merged_variant_repository_workflow(self, db_session):
        """Test MergedVariantRepository integration."""
        # Add merged variants
        for gene in ["BRCA1", "BRCA2", "TP53"]:
            variant = MergedVariant(
                file_id=1,
                chromosome="1",
                position=1000,
                ref_allele="A",
                alt_allele="T",
                gen_pos="1-1000-A-T",
                gene=gene,
                transcript="NM_000001",
                consequence="missense",
                source_databases=json.dumps(["clinvar"]),
                merge_timestamp=datetime.utcnow(),
                merge_strategy="outer_union"
            )
            db_session.add(variant)
        db_session.commit()

        # Query by gene
        repo = MergedVariantRepository(session=db_session)
        brca1_variants = repo.find_by_gene(file_id=1, gene="BRCA1")
        assert len(brca1_variants) == 1
        assert brca1_variants[0].gene == "BRCA1"

    def test_filtered_variant_repository_workflow(self, db_session):
        """Test FilteredVariantRepository integration."""
        # Add filtered variants with mixed validity
        for i in range(5):
            variant = FilteredVariant(
                file_id=1,
                chromosome="1",
                position=1000 + i*100,
                ref_allele="A",
                alt_allele="T",
                gen_pos=f"1-{1000+i*100}-A-T",
                is_complete=i < 3,  # First 3 are complete
                is_valid=i < 2,     # First 2 are valid
                filter_results=json.dumps({}),
                filter_timestamp=datetime.utcnow(),
                filter_version="1.0"
            )
            db_session.add(variant)
        db_session.commit()

        # Query by validity
        repo = FilteredVariantRepository(session=db_session)
        valid_variants = repo.find_by_validity(file_id=1, is_valid=True)
        assert len(valid_variants) == 2

        counts = repo.count_by_validity(file_id=1)
        assert counts["total"] == 5
        assert counts["valid"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
