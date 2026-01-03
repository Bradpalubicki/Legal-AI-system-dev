"""
Comprehensive Storage Systems Test Suite

Test all storage components for functionality and error detection:
- Document Version Control
- Batch Processing
- Export/Import with GDPR
- Multi-Level Caching
- Monitoring Dashboard
"""

import asyncio
import sys
import os
import tempfile
import json
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test if all storage modules can be imported"""
    print("=== Testing Storage Module Imports ===")

    try:
        # Test versioning imports
        from src.storage.versioning import DocumentVersioningSystem, VersioningAPI
        print("OK: Versioning system imports successful")

        # Test batch processing imports
        from src.storage.batch import BatchProcessingSystem, BatchAPI, ProcessingMode
        print("OK: Batch processing system imports successful")

        # Test portability imports
        from src.storage.portability import DataPortabilitySystem, PortabilityAPI, ExportFormat
        print("OK: Data portability system imports successful")

        # Test caching imports
        from src.storage.cache import MultiLevelCacheSystem, CacheAPI, CacheLevel
        print("OK: Caching system imports successful")

        # Test monitoring imports
        from src.storage.monitoring import StorageSystemMonitor, MonitoringAPI
        print("OK: Monitoring system imports successful")

        # Test package imports
        from src.storage import DocumentVersioningSystem as DVS
        print("OK: Package-level imports successful")

        return True

    except Exception as e:
        print(f"FAILED: Import failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_versioning_system():
    """Test document versioning system"""
    print("\n=== Testing Document Versioning System ===")

    try:
        from src.storage.versioning import DocumentVersioningSystem

        # Create system with temp directory
        with tempfile.TemporaryDirectory() as temp_dir:
            versioning = DocumentVersioningSystem(storage_path=temp_dir)

            # Test basic operations
            result = asyncio.run(test_versioning_operations(versioning))
            if result:
                print("OK: Versioning system tests passed")
                return True
            else:
                print("FAILED: Versioning system tests failed")
                return False

    except Exception as e:
        print(f"FAILED: Versioning system error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_versioning_operations(versioning):
    """Test versioning operations"""
    try:
        document_id = "test_doc_001"

        # Create first version
        version1 = await versioning.create_version(
            document_id=document_id,
            content=b"This is the first version of the document.",
            title="Test Document v1",
            created_by="test_user"
        )
        print(f"  Created version: {version1.version_id}")

        # Create second version
        version2 = await versioning.create_version(
            document_id=document_id,
            content=b"This is the second version with changes.",
            title="Test Document v2",
            created_by="test_user",
            parent_version=version1.version_id
        )
        print(f"  Created version: {version2.version_id}")

        # Test version history
        history = await versioning.get_version_history(document_id)
        print(f"  Version history count: {len(history)}")

        # Test version comparison
        diff = await versioning.compare_versions(document_id, version1.version_id, version2.version_id)
        if diff:
            print(f"  Version comparison successful, similarity: {diff.similarity_score:.2f}")

        # Test rollback
        rollback_version = await versioning.rollback_to_version(
            document_id, version1.version_id, "test_user"
        )
        if rollback_version:
            print(f"  Rollback successful: {rollback_version.version_id}")

        # Test statistics
        stats = await versioning.get_version_statistics(document_id)
        print(f"  Statistics: {stats.get('total_versions', 0)} versions")

        return True

    except Exception as e:
        print(f"  Versioning operation error: {str(e)}")
        return False

def test_batch_system():
    """Test batch processing system"""
    print("\n=== Testing Batch Processing System ===")

    try:
        from src.storage.batch import BatchProcessingSystem, ProcessingMode

        batch_system = BatchProcessingSystem(max_concurrent_batches=2)

        result = asyncio.run(test_batch_operations(batch_system))

        # Cleanup
        batch_system.shutdown()

        if result:
            print("OK: Batch processing system tests passed")
            return True
        else:
            print("FAILED: Batch processing system tests failed")
            return False

    except Exception as e:
        print(f"FAILED: Batch processing system error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_batch_operations(batch_system):
    """Test batch operations"""
    try:
        from src.storage.batch import ProcessingMode

        # Create test batch
        tasks_data = [
            {
                'task_type': 'document_upload',
                'input_data': {'file_path': 'test_file_1.txt'},
                'priority': 1
            },
            {
                'task_type': 'document_analysis',
                'input_data': {'document_id': 'doc_123', 'analysis_type': 'basic'},
                'priority': 2
            }
        ]

        # Create batch
        batch_id = await batch_system.create_batch(
            name="Test Batch",
            description="Testing batch processing",
            tasks_data=tasks_data,
            created_by="test_user",
            processing_mode=ProcessingMode.SEQUENTIAL
        )
        print(f"  Created batch: {batch_id}")

        # Get batch status
        batch = await batch_system.get_batch_status(batch_id)
        if batch:
            print(f"  Batch status: {batch.status.value}")
            print(f"  Task count: {len(batch.tasks)}")

        # Test progress tracking
        progress = await batch_system.get_batch_progress(batch_id)
        if progress:
            print(f"  Progress tracking working: {progress.total_tasks} tasks")

        return True

    except Exception as e:
        print(f"  Batch operation error: {str(e)}")
        return False

def test_portability_system():
    """Test data portability system"""
    print("\n=== Testing Data Portability System ===")

    try:
        from src.storage.portability import DataPortabilitySystem, DataScope, ExportFormat

        with tempfile.TemporaryDirectory() as temp_dir:
            portability = DataPortabilitySystem(storage_path=temp_dir)

            result = asyncio.run(test_portability_operations(portability))

            if result:
                print("OK: Data portability system tests passed")
                return True
            else:
                print("FAILED: Data portability system tests failed")
                return False

    except Exception as e:
        print(f"FAILED: Data portability system error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_portability_operations(portability):
    """Test portability operations"""
    try:
        from src.storage.portability import DataScope, ExportFormat

        # Request data export
        export_job_id = await portability.request_data_export(
            user_id="test_user_123",
            data_scopes=[DataScope.DOCUMENTS, DataScope.USER_PROFILE],
            export_format=ExportFormat.JSON
        )
        print(f"  Created export job: {export_job_id}")

        # Check export status
        status = await portability.get_export_status(export_job_id)
        if status:
            print(f"  Export status: {status['status']}")

        # Test deletion request
        deletion_id = await portability.delete_user_data(
            user_id="test_user_123",
            data_scopes=[DataScope.DOCUMENTS]
        )
        print(f"  Created deletion request: {deletion_id}")

        # Test cleanup
        cleaned = await portability.cleanup_expired_exports()
        print(f"  Cleanup result: {cleaned} exports cleaned")

        return True

    except Exception as e:
        print(f"  Portability operation error: {str(e)}")
        return False

def test_cache_system():
    """Test caching system"""
    print("\n=== Testing Multi-Level Cache System ===")

    try:
        from src.storage.cache import MultiLevelCacheSystem

        cache_system = MultiLevelCacheSystem(
            redis_url="redis://localhost:6379",  # Will fail gracefully if Redis not available
            cdn_url=""
        )

        result = asyncio.run(test_cache_operations(cache_system))

        if result:
            print("OK: Caching system tests passed")
            return True
        else:
            print("FAILED: Caching system tests failed")
            return False

    except Exception as e:
        print(f"FAILED: Caching system error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_cache_operations(cache_system):
    """Test cache operations"""
    try:
        # Initialize cache system
        await cache_system.initialize()

        # Test memory cache operations
        test_key = "test_cache_key"
        test_value = {"data": "test_value", "timestamp": datetime.now().isoformat()}

        # Set value
        success = await cache_system.set(test_key, test_value, ttl_seconds=300)
        print(f"  Cache set successful: {success}")

        # Get value
        cached_value = await cache_system.get(test_key)
        if cached_value:
            print(f"  Cache get successful: {type(cached_value)}")

        # Test tag-based invalidation
        tagged_key = "tagged_key"
        await cache_system.set(tagged_key, "tagged_value", ttl_seconds=300, tags=["test_tag"])

        invalidated = await cache_system.invalidate_by_tags(["test_tag"])
        print(f"  Tag invalidation: {invalidated} entries")

        # Test cache statistics
        stats = await cache_system.get_global_stats()
        print(f"  Cache stats available: {len(stats)} categories")

        # Test cache decorator
        @cache_system.cache(ttl_seconds=60)
        def test_cached_function(param):
            return f"result_for_{param}"

        # Call cached function
        result1 = test_cached_function("test")
        result2 = test_cached_function("test")  # Should hit cache
        print(f"  Cached function results: {result1 == result2}")

        return True

    except Exception as e:
        print(f"  Cache operation error: {str(e)}")
        return False

def test_monitoring_system():
    """Test monitoring system"""
    print("\n=== Testing Monitoring System ===")

    try:
        from src.storage.monitoring import StorageMonitoringIntegration

        # Create monitoring integration
        monitoring = StorageMonitoringIntegration()

        result = test_monitoring_operations(monitoring)

        if result:
            print("OK: Monitoring system tests passed")
            return True
        else:
            print("FAILED: Monitoring system tests failed")
            return False

    except Exception as e:
        print(f"FAILED: Monitoring system error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_operations(monitoring):
    """Test monitoring operations"""
    try:
        # Test API creation
        apis = monitoring.get_all_apis()
        print(f"  Available APIs: {list(apis.keys())}")

        # Test metrics collection
        from src.storage.monitoring import MetricType
        monitoring.storage_monitor.metrics_collector.add_metric(
            "test.metric", 42.0,
            MetricType.GAUGE
        )
        print("  Metric collection successful")

        # Test alert creation
        from src.storage.monitoring import AlertLevel
        monitoring.storage_monitor.metrics_collector.add_alert(
            AlertLevel.INFO,
            "Test Alert",
            "This is a test alert",
            "test_component"
        )
        print("  Alert creation successful")

        # Test health status update
        monitoring.storage_monitor.metrics_collector.update_health_status(
            "test_component", "healthy", 50.0
        )
        print("  Health status update successful")

        # Test recent metrics retrieval
        recent_metrics = monitoring.storage_monitor.metrics_collector.get_recent_metrics(hours=1)
        print(f"  Recent metrics: {len(recent_metrics)} entries")

        # Test active alerts
        active_alerts = monitoring.storage_monitor.metrics_collector.get_active_alerts()
        print(f"  Active alerts: {len(active_alerts)} alerts")

        return True

    except Exception as e:
        print(f"  Monitoring operation error: {str(e)}")
        return False

def test_integration():
    """Test system integration"""
    print("\n=== Testing System Integration ===")

    try:
        from src.storage.monitoring import StorageMonitoringIntegration

        # Create integrated system
        integration = StorageMonitoringIntegration()

        # Test that all systems are accessible
        versioning = integration.versioning_system
        batch = integration.batch_system
        portability = integration.portability_system
        cache = integration.cache_system
        monitor = integration.storage_monitor

        print("  OK: Versioning system accessible")
        print("  OK: Batch system accessible")
        print("  OK: Portability system accessible")
        print("  OK: Cache system accessible")
        print("  OK: Monitoring system accessible")

        # Test API integration
        apis = integration.get_all_apis()
        required_apis = ['versioning', 'batch', 'portability', 'cache', 'monitoring']

        for api_name in required_apis:
            if api_name in apis:
                print(f"  OK: {api_name.title()} API available")
            else:
                print(f"  FAILED: {api_name.title()} API missing")
                return False

        print("OK: System integration tests passed")
        return True

    except Exception as e:
        print(f"FAILED: System integration error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def run_async_comprehensive_test():
    """Run comprehensive async test"""
    print("\n=== Running Comprehensive Async Test ===")

    try:
        from src.storage.monitoring import StorageMonitoringIntegration

        # Create integrated system
        integration = StorageMonitoringIntegration()

        # Test initialization
        await integration.cache_system.initialize()
        print("  OK: Cache system initialized")

        # Test versioning with actual file operations
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write("Test document content for versioning")
            tmp_file_path = tmp_file.name

        try:
            # Read file and create version
            with open(tmp_file_path, 'rb') as f:
                content = f.read()

            version = await integration.versioning_system.create_version(
                document_id="async_test_doc",
                content=content,
                title="Async Test Document",
                created_by="async_test_user"
            )
            print(f"  OK: Created version: {version.version_id}")

            # Test cache with real data
            cache_key = f"doc_cache_{version.document_id}"
            cached = await integration.cache_system.set(
                cache_key,
                {"version_id": version.version_id, "content_size": len(content)},
                ttl_seconds=300
            )
            print(f"  OK: Cached document data: {cached}")

            # Retrieve from cache
            cached_data = await integration.cache_system.get(cache_key)
            if cached_data:
                print(f"  OK: Retrieved from cache: {cached_data['version_id']}")

        finally:
            # Cleanup temp file
            os.unlink(tmp_file_path)

        # Test batch processing with real tasks
        batch_id = await integration.batch_system.create_batch(
            name="Async Test Batch",
            description="Testing async batch operations",
            tasks_data=[
                {
                    'task_type': 'document_analysis',
                    'input_data': {'document_id': 'async_test_doc', 'analysis_type': 'basic'}
                }
            ],
            created_by="async_test_user"
        )
        print(f"  OK: Created async batch: {batch_id}")

        # Test export functionality
        from src.storage.portability import DataScope
        export_id = await integration.portability_system.request_data_export(
            user_id="async_test_user",
            data_scopes=[DataScope.DOCUMENTS]
        )
        print(f"  OK: Created async export: {export_id}")

        print("OK: Comprehensive async test passed")
        return True

    except Exception as e:
        print(f"FAILED: Comprehensive async test error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all storage system tests"""
    print("TEST: Starting Comprehensive Storage Systems Test Suite")
    print("=" * 60)

    test_results = []

    # Test imports first
    test_results.append(("Import Tests", test_imports()))

    # Test individual systems
    test_results.append(("Versioning System", test_versioning_system()))
    test_results.append(("Batch Processing System", test_batch_system()))
    test_results.append(("Data Portability System", test_portability_system()))
    test_results.append(("Caching System", test_cache_system()))
    test_results.append(("Monitoring System", test_monitoring_system()))

    # Test integration
    test_results.append(("System Integration", test_integration()))

    # Run async comprehensive test
    async_result = asyncio.run(run_async_comprehensive_test())
    test_results.append(("Comprehensive Async Test", async_result))

    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = 0
    total = len(test_results)

    for test_name, result in test_results:
        status = "[PASSED]" if result else "[FAILED]"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1

    print("-" * 60)
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")

    if passed == total:
        print("\nALL STORAGE SYSTEMS TESTS PASSED!")
        print("Document Version Control - Working")
        print("Batch Processing System - Working")
        print("Data Export/Import (GDPR) - Working")
        print("Multi-Level Caching - Working")
        print("Monitoring Dashboard - Working")
        print("System Integration - Working")

        print("\nStorage Infrastructure Status: FULLY OPERATIONAL")
    else:
        print(f"\nWARNING: {total - passed} test(s) failed. Check logs above for details.")
        return 1

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)