#!/usr/bin/env python3
"""Test script for MCP server functionality."""

import sys
import json
from pathlib import Path

# Add paths
SCRIPT_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(SCRIPT_DIR / "src"))
sys.path.insert(0, str(SCRIPT_DIR / "scripts"))

def test_server_import():
    """Test that the server can be imported without errors."""
    try:
        from src.server import mcp
        print("✅ Server import successful")
        return True
    except Exception as e:
        print(f"❌ Server import failed: {e}")
        return False

def test_script_imports():
    """Test that script functions can be imported."""
    try:
        from analyze_peptides import run_analyze_peptides
        from generate_sequences import run_generate_sequences
        print("✅ Script imports successful")
        return True
    except Exception as e:
        print(f"❌ Script imports failed: {e}")
        return False

def test_job_manager():
    """Test job manager functionality."""
    try:
        from src.jobs.manager import job_manager

        # Test basic job manager functions
        jobs = job_manager.list_jobs()
        print(f"✅ Job manager working, found {len(jobs.get('jobs', []))} existing jobs")
        return True
    except Exception as e:
        print(f"❌ Job manager test failed: {e}")
        return False

def test_analyze_peptides():
    """Test peptide analysis function directly."""
    try:
        from analyze_peptides import run_analyze_peptides

        # Test with demo data
        result = run_analyze_peptides()  # Should use demo data

        if result and "metadata" in result:
            print(f"✅ Peptide analysis working - processed {result['metadata'].get('sequences_analyzed', '?')} sequences")
            return True
        else:
            print("❌ Peptide analysis returned unexpected result")
            return False
    except Exception as e:
        print(f"❌ Peptide analysis test failed: {e}")
        return False

def test_generate_sequences():
    """Test sequence generation function directly."""
    try:
        from generate_sequences import run_generate_sequences

        # Test with small number
        result = run_generate_sequences(num_samples=3)

        if result and "sequences" in result:
            print(f"✅ Sequence generation working - generated {len(result['sequences'])} sequences")
            return True
        else:
            print("❌ Sequence generation returned unexpected result")
            return False
    except Exception as e:
        print(f"❌ Sequence generation test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing MCP Server Functionality")
    print("=" * 40)

    tests = [
        ("Server Import", test_server_import),
        ("Script Imports", test_script_imports),
        ("Job Manager", test_job_manager),
        ("Analyze Peptides", test_analyze_peptides),
        ("Generate Sequences", test_generate_sequences)
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        if test_func():
            passed += 1

    print("\n" + "=" * 40)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! MCP server is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())