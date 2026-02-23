#!/usr/bin/env python3
"""Automated integration test runner for PepFlowww MCP server."""

import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

class MCPIntegrationTestRunner:
    """Test runner for MCP server integration validation."""

    def __init__(self, server_path: str, env_path: str):
        self.server_path = Path(server_path).resolve()
        self.env_path = Path(env_path).resolve()
        self.python_path = self.env_path / "bin" / "python"
        self.results = {
            "test_date": datetime.now().isoformat(),
            "server_path": str(self.server_path),
            "env_path": str(self.env_path),
            "python_path": str(self.python_path),
            "tests": {},
            "issues": [],
            "summary": {}
        }

    def log_test(self, test_name: str, status: str, output: str = "", error: str = "", duration: float = 0):
        """Log a test result."""
        self.results["tests"][test_name] = {
            "status": status,
            "output": output,
            "error": error,
            "duration": duration
        }

    def run_command(self, command: list, timeout: int = 30) -> tuple:
        """Run a command and return (success, stdout, stderr, duration)."""
        start_time = time.time()
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.server_path.parent
            )
            duration = time.time() - start_time
            return result.returncode == 0, result.stdout, result.stderr, duration
        except subprocess.TimeoutExpired:
            duration = time.time() - start_time
            return False, "", f"Command timed out after {timeout}s", duration
        except Exception as e:
            duration = time.time() - start_time
            return False, "", str(e), duration

    def test_environment_setup(self) -> bool:
        """Test that the environment is properly set up."""
        print("Testing environment setup...")

        # Test Python executable exists
        if not self.python_path.exists():
            self.log_test("python_executable", "failed", error=f"Python not found at {self.python_path}")
            return False

        # Test Python version
        success, output, error, duration = self.run_command([str(self.python_path), "--version"])
        if success:
            self.log_test("python_version", "passed", output.strip(), duration=duration)
        else:
            self.log_test("python_version", "failed", error=error, duration=duration)
            return False

        # Test required packages
        packages = ["fastmcp", "numpy", "pandas"]
        for package in packages:
            success, output, error, duration = self.run_command([
                str(self.python_path), "-c", f"import {package}; print(f'{package} OK')"
            ])
            if success:
                self.log_test(f"import_{package}", "passed", output.strip(), duration=duration)
            else:
                self.log_test(f"import_{package}", "failed", error=error, duration=duration)
                return False

        return True

    def test_server_startup(self) -> bool:
        """Test that server starts without errors."""
        print("Testing server startup...")

        # Test syntax
        success, output, error, duration = self.run_command([
            str(self.python_path), "-m", "py_compile", "src/server.py"
        ])
        if success:
            self.log_test("server_syntax", "passed", duration=duration)
        else:
            self.log_test("server_syntax", "failed", error=error, duration=duration)
            return False

        # Test import
        success, output, error, duration = self.run_command([
            str(self.python_path), "-c", "from src.server import mcp; print('Server imports OK')"
        ])
        if success:
            self.log_test("server_import", "passed", output.strip(), duration=duration)
        else:
            self.log_test("server_import", "failed", error=error, duration=duration)
            return False

        return True

    def test_mcp_registration(self) -> bool:
        """Test MCP server registration with Claude Code."""
        print("Testing MCP registration...")

        # Check if server is registered
        success, output, error, duration = self.run_command(["claude", "mcp", "list"], timeout=10)
        if success and "pepflowww-tools" in output and "✓ Connected" in output:
            self.log_test("mcp_registration", "passed", output, duration=duration)
            return True
        else:
            self.log_test("mcp_registration", "failed", output + error, duration=duration)
            return False

    def test_tool_functionality(self) -> bool:
        """Test basic tool functionality."""
        print("Testing tool functionality...")

        # Test that tools are accessible via the existing test script
        success, output, error, duration = self.run_command([
            str(self.python_path), "test_server_tools.py"
        ], timeout=30)

        if success and "MCP server tools are ready!" in output:
            self.log_test("tool_functionality", "passed", output, duration=duration)
            return True
        else:
            self.log_test("tool_functionality", "failed", error, duration=duration)
            return False

    def test_job_system(self) -> bool:
        """Test job management system."""
        print("Testing job system...")

        # Test job manager import
        success, output, error, duration = self.run_command([
            str(self.python_path), "-c",
            "from src.jobs.manager import JobManager; jm = JobManager(); print('Job manager OK')"
        ])

        if success:
            self.log_test("job_manager", "passed", output.strip(), duration=duration)
        else:
            self.log_test("job_manager", "failed", error, duration=duration)
            return False

        # Test jobs directory exists
        jobs_dir = self.server_path.parent / "jobs"
        if jobs_dir.exists():
            self.log_test("jobs_directory", "passed", f"Jobs directory exists at {jobs_dir}")
        else:
            jobs_dir.mkdir(exist_ok=True)
            self.log_test("jobs_directory", "created", f"Created jobs directory at {jobs_dir}")

        return True

    def test_demo_data(self) -> bool:
        """Test demo data availability."""
        print("Testing demo data...")

        # Check if demo data files exist
        examples_dir = self.server_path.parent / "examples" / "data"
        if examples_dir.exists():
            seq_files = list(examples_dir.glob("sequences/*.fasta"))
            if seq_files:
                self.log_test("demo_data", "passed", f"Found {len(seq_files)} demo sequence files")
                return True
            else:
                self.log_test("demo_data", "warning", "Examples directory exists but no sequence files found")
                return True
        else:
            self.log_test("demo_data", "warning", "Examples directory not found - demo data unavailable")
            return True  # Not critical for basic functionality

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        print("=" * 60)
        print("PepFlowww MCP Server Integration Tests")
        print("=" * 60)

        tests = [
            ("Environment Setup", self.test_environment_setup),
            ("Server Startup", self.test_server_startup),
            ("MCP Registration", self.test_mcp_registration),
            ("Tool Functionality", self.test_tool_functionality),
            ("Job System", self.test_job_system),
            ("Demo Data", self.test_demo_data)
        ]

        all_passed = True
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                if not test_func():
                    all_passed = False
                    print(f"❌ {test_name} failed")
                else:
                    print(f"✅ {test_name} passed")
            except Exception as e:
                all_passed = False
                self.log_test(test_name.lower().replace(" ", "_"), "error", error=str(e))
                print(f"💥 {test_name} error: {e}")

        return all_passed

    def generate_report(self) -> str:
        """Generate comprehensive test report."""
        total = len(self.results["tests"])
        passed = sum(1 for t in self.results["tests"].values() if t.get("status") == "passed")
        failed = sum(1 for t in self.results["tests"].values() if t.get("status") == "failed")
        warnings = sum(1 for t in self.results["tests"].values() if t.get("status") == "warning")
        errors = sum(1 for t in self.results["tests"].values() if t.get("status") == "error")

        self.results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "errors": errors,
            "pass_rate": f"{passed/total*100:.1f}%" if total > 0 else "N/A",
            "overall_status": "PASSED" if failed == 0 and errors == 0 else "FAILED"
        }

        # Generate markdown report
        report = f"""# PepFlowww MCP Server Integration Test Report

## Test Information
- **Test Date**: {self.results['test_date']}
- **Server Name**: pepflowww-tools
- **Server Path**: {self.results['server_path']}
- **Environment Path**: {self.results['env_path']}
- **Python Path**: {self.results['python_path']}

## Test Results Summary

| Metric | Value |
|--------|-------|
| Total Tests | {total} |
| Passed | {passed} |
| Failed | {failed} |
| Warnings | {warnings} |
| Errors | {errors} |
| Pass Rate | {self.results['summary']['pass_rate']} |
| **Overall Status** | **{self.results['summary']['overall_status']}** |

## Detailed Results

"""

        for test_name, test_data in self.results["tests"].items():
            status_emoji = {
                "passed": "✅",
                "failed": "❌",
                "warning": "⚠️",
                "error": "💥",
                "created": "🆕"
            }.get(test_data["status"], "❓")

            report += f"### {status_emoji} {test_name.replace('_', ' ').title()}\n"
            report += f"- **Status**: {test_data['status']}\n"
            if test_data.get("duration"):
                report += f"- **Duration**: {test_data['duration']:.2f}s\n"
            if test_data.get("output"):
                report += f"- **Output**: {test_data['output']}\n"
            if test_data.get("error"):
                report += f"- **Error**: {test_data['error']}\n"
            report += "\n"

        report += f"""## Next Steps

### If Tests Passed:
1. Proceed with manual testing using the prompts in `tests/test_prompts.md`
2. Test sync tools for immediate response
3. Test async job submission and monitoring
4. Test batch processing capabilities
5. Run real-world scenarios

### If Tests Failed:
1. Review failed test details above
2. Check environment activation: `mamba activate {self.env_path}`
3. Verify server registration: `claude mcp list`
4. Check Python dependencies: `pip list | grep -E "fastmcp|numpy|pandas"`
5. Restart Claude Code after fixing issues

## Test Artifacts
- **Test Script**: `tests/run_integration_tests.py`
- **Test Prompts**: `tests/test_prompts.md`
- **Full Results**: `reports/step7_integration.json`

---
*Generated by PepFlowww MCP Integration Test Runner v1.0*
"""

        return report

def main():
    """Main test runner function."""
    if len(sys.argv) < 3:
        print("Usage: python run_integration_tests.py <server_path> <env_path>")
        print("Example: python run_integration_tests.py src/server.py ./env")
        sys.exit(1)

    server_path = sys.argv[1]
    env_path = sys.argv[2]

    runner = MCPIntegrationTestRunner(server_path, env_path)

    # Run all tests
    success = runner.run_all_tests()

    # Generate reports
    report_md = runner.generate_report()

    # Save reports
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)

    (reports_dir / "step7_integration.md").write_text(report_md)
    (reports_dir / "step7_integration.json").write_text(json.dumps(runner.results, indent=2))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Overall Status: {runner.results['summary']['overall_status']}")
    print(f"Pass Rate: {runner.results['summary']['pass_rate']}")
    print(f"Detailed report saved to: reports/step7_integration.md")
    print(f"Raw results saved to: reports/step7_integration.json")

    if success:
        print("\n🎉 All integration tests passed! Server is ready for use with Claude Code.")
        print("\nNext steps:")
        print("1. Test tools manually using prompts in tests/test_prompts.md")
        print("2. Run: claude")
        print("3. Try: 'What tools are available from pepflowww-tools?'")
    else:
        print("\n❌ Some tests failed. Please review the report and fix issues.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())