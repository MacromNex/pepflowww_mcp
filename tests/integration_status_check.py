#!/usr/bin/env python3
"""
PepFlowww MCP Integration Status Check
=====================================

Quick verification script to check MCP server integration status.
Run this anytime to verify the server is properly configured and working.
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

def run_command(cmd, timeout=10):
    """Run command and return (success, output, error)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def check_status():
    """Check integration status and return summary."""
    print("🧪 PepFlowww MCP Integration Status Check")
    print("=" * 50)
    print(f"Check Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    checks = []

    # 1. Check if we're in the right directory
    print("📁 Environment Check...")
    if Path("src/server.py").exists() and Path("env").exists():
        print("  ✅ Project structure found")
        checks.append(("Project Structure", True))
    else:
        print("  ❌ Project structure not found - run from project root")
        checks.append(("Project Structure", False))
        return checks

    # 2. Check Python environment
    print("🐍 Python Environment...")
    success, output, error = run_command("python -c 'import sys; print(sys.version)'")
    if success:
        python_version = output.strip().split()[0]
        print(f"  ✅ Python {python_version}")
        checks.append(("Python Environment", True))
    else:
        print(f"  ❌ Python check failed: {error}")
        checks.append(("Python Environment", False))

    # 3. Check server imports
    print("📦 Server Imports...")
    success, output, error = run_command("python -c 'from src.server import mcp; print(\"Server imports OK\")'")
    if success:
        print("  ✅ Server imports successfully")
        checks.append(("Server Imports", True))
    else:
        print(f"  ❌ Server import failed: {error}")
        checks.append(("Server Imports", False))

    # 4. Check Claude Code registration
    print("🔧 Claude Code Integration...")
    success, output, error = run_command("claude mcp list")
    if success and "pepflowww-tools" in output and "Connected" in output:
        print("  ✅ Registered with Claude Code and connected")
        checks.append(("Claude Code Integration", True))
    else:
        print("  ❌ Not properly registered with Claude Code")
        print(f"     Run: claude mcp add pepflowww-tools -- $(pwd)/env/bin/python $(pwd)/src/server.py")
        checks.append(("Claude Code Integration", False))

    # 5. Check tool functionality
    print("🛠  Tool Functionality...")
    success, output, error = run_command("python test_server_tools.py")
    if success and "MCP server tools are ready!" in output:
        print("  ✅ All 12 tools accessible and ready")
        checks.append(("Tool Functionality", True))
    else:
        print("  ❌ Tool functionality test failed")
        checks.append(("Tool Functionality", False))

    # 6. Check job system
    print("⚙️  Job Management System...")
    success, output, error = run_command("python -c 'from src.jobs.manager import job_manager; print(\"Job manager:\", len(job_manager.list_jobs().get(\"jobs\", [])), \"jobs found\")'")
    if success:
        print("  ✅ Job management system working")
        checks.append(("Job Management", True))
    else:
        print("  ❌ Job management system error")
        checks.append(("Job Management", False))

    # 7. Check Gemini CLI (optional)
    print("🔮 Gemini CLI Integration...")
    success, output, error = run_command("gemini mcp list")
    if success and "pepflowww-tools" in output and "Connected" in output:
        print("  ✅ Registered with Gemini CLI and connected")
        checks.append(("Gemini CLI Integration", True))
    elif success:
        print("  ⚠️  Gemini CLI available but pepflowww-tools not registered")
        print("     Run: gemini mcp add pepflowww-tools $(pwd)/env/bin/python $(pwd)/src/server.py")
        checks.append(("Gemini CLI Integration", False))
    else:
        print("  ⚠️  Gemini CLI not available (optional)")
        checks.append(("Gemini CLI Integration", None))  # Not critical

    # 8. Quick functional test
    print("🧬 Quick Functional Test...")
    success, output, error = run_command("python test_mcp.py", timeout=30)
    if success and "All tests passed!" in output:
        print("  ✅ Functional test passed - server working correctly")
        checks.append(("Functional Test", True))
    else:
        print("  ❌ Functional test failed")
        checks.append(("Functional Test", False))

    return checks

def print_summary(checks):
    """Print summary and recommendations."""
    print()
    print("📊 INTEGRATION STATUS SUMMARY")
    print("=" * 50)

    passed = sum(1 for name, status in checks if status is True)
    failed = sum(1 for name, status in checks if status is False)
    optional = sum(1 for name, status in checks if status is None)
    total = len(checks) - optional

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {failed}/{total}")
    if optional > 0:
        print(f"⚠️  Optional: {optional}")

    pass_rate = (passed / total * 100) if total > 0 else 0
    print(f"📈 Pass Rate: {pass_rate:.1f}%")

    print()
    if failed == 0:
        print("🎉 ALL CRITICAL SYSTEMS WORKING!")
        print("✅ MCP server is ready for production use")
        print()
        print("Quick Usage:")
        print("  • Claude Code: claude")
        print("  • Ask: 'What tools are available from pepflowww-tools?'")
        print("  • Try: 'Analyze demo peptides for drug properties'")
    else:
        print("⚠️  SOME SYSTEMS NEED ATTENTION")
        print()
        print("Failed checks:")
        for name, status in checks:
            if status is False:
                print(f"  ❌ {name}")

        print()
        print("Recommended fixes:")
        print("  1. Ensure you're in the correct project directory")
        print("  2. Activate the environment: mamba activate ./env")
        print("  3. Register with Claude Code: claude mcp add pepflowww-tools -- $(pwd)/env/bin/python $(pwd)/src/server.py")
        print("  4. Check error messages above for specific issues")

    print()
    print("📚 Documentation:")
    print("  • Integration Report: reports/step7_integration_final.md")
    print("  • Test Prompts: tests/test_prompts.md")
    print("  • Project README: README.md")

def main():
    """Main function."""
    checks = check_status()
    print_summary(checks)

    # Exit with appropriate code
    failed = sum(1 for name, status in checks if status is False)
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())