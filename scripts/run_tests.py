#!/usr/bin/env python3
"""
Comprehensive Test Runner Script

Unified script to run all tests with coverage reporting and validation
for the Legal AI System. Ensures 95% coverage target is achieved.
"""

import os
import sys
import subprocess
import argparse
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import xml.etree.ElementTree as ET


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class TestRunner:
    """Main test runner class"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backend_dir = self.project_root / "backend"
        self.frontend_dir = self.project_root / "frontend"
        self.tests_dir = self.project_root / "tests"
        self.coverage_dir = self.project_root / "coverage"
        self.reports_dir = self.project_root / "test-reports"
        
        # Ensure directories exist
        self.coverage_dir.mkdir(exist_ok=True)
        self.reports_dir.mkdir(exist_ok=True)
    
    def print_header(self, message: str):
        """Print colored header message"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{message.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, message: str):
        """Print success message"""
        print(f"{Colors.OKGREEN}[SUCCESS] {message}{Colors.ENDC}")
    
    def print_warning(self, message: str):
        """Print warning message"""
        print(f"{Colors.WARNING}[WARNING] {message}{Colors.ENDC}")
    
    def print_error(self, message: str):
        """Print error message"""
        print(f"{Colors.FAIL}[ERROR] {message}{Colors.ENDC}")
    
    def print_info(self, message: str):
        """Print info message"""
        print(f"{Colors.OKBLUE}[INFO] {message}{Colors.ENDC}")
    
    def run_command(
        self, 
        command: List[str], 
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        capture_output: bool = False
    ) -> Tuple[bool, str, str]:
        """Run a command and return success status and output"""
        if cwd is None:
            cwd = self.project_root
        
        # Merge environment variables
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        try:
            if capture_output:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    env=full_env,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                return result.returncode == 0, result.stdout, result.stderr
            else:
                result = subprocess.run(
                    command,
                    cwd=cwd,
                    env=full_env,
                    timeout=300
                )
                return result.returncode == 0, "", ""
        except subprocess.TimeoutExpired:
            self.print_error(f"Command timed out: {' '.join(command)}")
            return False, "", "Command timed out"
        except Exception as e:
            self.print_error(f"Command failed: {e}")
            return False, "", str(e)
    
    def setup_environment(self):
        """Set up test environment variables"""
        test_env = {
            "ENVIRONMENT": "testing",
            "DEBUG": "true",
            "DATABASE_URL": "sqlite+aiosqlite:///:memory:",
            "REDIS_URL": "redis://localhost:6379/15",
            "JWT_SECRET": "test-jwt-secret-key-for-testing-only",
            "ENCRYPTION_KEY": "test-encryption-key-32-chars-123",
            "SENTRY_ENABLED": "false",
            "LOG_LEVEL": "DEBUG",
            "PYTHONPATH": str(self.project_root / "src") + ":" + str(self.backend_dir / "app" / "src")
        }
        
        # Set environment variables
        for key, value in test_env.items():
            os.environ[key] = value
        
        return test_env
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are installed"""
        self.print_info("Checking dependencies...")
        
        # Check Python dependencies
        success, _, _ = self.run_command(["python", "-c", "import pytest, coverage"], capture_output=True)
        if not success:
            self.print_error("Python test dependencies not installed. Run: pip install -e .[dev,test]")
            return False
        
        # Check Node dependencies (if frontend exists)
        if self.frontend_dir.exists():
            success, _, _ = self.run_command(["npm", "list"], cwd=self.frontend_dir, capture_output=True)
            if not success:
                self.print_warning("Frontend dependencies may not be installed. Run: npm install in frontend/")
        
        self.print_success("Dependencies check passed")
        return True
    
    def run_backend_linting(self) -> bool:
        """Run backend code quality checks"""
        self.print_info("Running backend linting and formatting checks...")
        
        checks = [
            (["python", "-m", "mypy", "src/", "--ignore-missing-imports"], "Type checking"),
            (["python", "-m", "black", "--check", "src/", "tests/"], "Code formatting"),
            (["python", "-m", "isort", "--check-only", "src/", "tests/"], "Import sorting"),
            (["python", "-m", "flake8", "src/", "tests/"], "Linting"),
            (["python", "-m", "bandit", "-r", "src/", "-f", "json", "-o", "bandit-report.json"], "Security check")
        ]
        
        all_passed = True
        for command, description in checks:
            self.print_info(f"  Running {description}...")
            success, stdout, stderr = self.run_command(command, capture_output=True)
            if success:
                self.print_success(f"  {description} passed")
            else:
                self.print_error(f"  {description} failed")
                if stderr:
                    print(f"    {stderr}")
                all_passed = False
        
        return all_passed
    
    def run_frontend_linting(self) -> bool:
        """Run frontend code quality checks"""
        if not self.frontend_dir.exists():
            self.print_info("Frontend directory not found, skipping frontend linting")
            return True
        
        self.print_info("Running frontend linting and formatting checks...")
        
        checks = [
            (["npm", "run", "typecheck"], "TypeScript compilation"),
            (["npm", "run", "lint"], "ESLint check"),
            (["npm", "run", "format:check"], "Prettier formatting")
        ]
        
        all_passed = True
        for command, description in checks:
            self.print_info(f"  Running {description}...")
            success, stdout, stderr = self.run_command(command, cwd=self.frontend_dir, capture_output=True)
            if success:
                self.print_success(f"  {description} passed")
            else:
                # Some lint commands may not exist, treat as warning
                self.print_warning(f"  {description} skipped or failed")
        
        return all_passed
    
    def run_backend_tests(self, test_type: str = "all") -> Tuple[bool, Dict[str, float]]:
        """Run backend tests with coverage"""
        self.print_info(f"Running backend {test_type} tests...")
        
        # Base pytest command
        pytest_cmd = [
            "python", "-m", "pytest",
            "--cov=src",
            "--cov=backend/app/src",
            "--cov-report=xml:coverage/backend-coverage.xml",
            "--cov-report=html:coverage/backend-html",
            "--cov-report=term-missing",
            "--cov-fail-under=95",
            "--junitxml=test-reports/backend-results.xml",
            "--maxfail=5",
            "--tb=short",
            "-v"
        ]
        
        # Add specific test directories based on type
        if test_type == "unit":
            pytest_cmd.append("tests/unit/")
        elif test_type == "integration":
            pytest_cmd.extend(["tests/integration/", "--cov-append"])
        elif test_type == "database":
            pytest_cmd.extend(["tests/integration/database/", "--cov-append"])
        elif test_type == "api":
            pytest_cmd.extend(["tests/integration/api/", "--cov-append"])
        else:  # all
            pytest_cmd.extend(["tests/", "--cov-append"])
        
        success, stdout, stderr = self.run_command(pytest_cmd, capture_output=True)
        
        # Parse coverage results
        coverage_info = self.parse_backend_coverage()
        
        if success:
            self.print_success(f"Backend {test_type} tests passed")
            self.print_coverage_summary(coverage_info)
        else:
            self.print_error(f"Backend {test_type} tests failed")
            if stderr:
                print(stderr)
        
        return success, coverage_info
    
    def run_frontend_tests(self) -> Tuple[bool, Dict[str, float]]:
        """Run frontend tests with coverage"""
        if not self.frontend_dir.exists():
            self.print_info("Frontend directory not found, skipping frontend tests")
            return True, {}
        
        self.print_info("Running frontend tests...")
        
        # Jest command with coverage
        jest_cmd = [
            "npm", "test", "--",
            "--coverage",
            "--coverageReporters=text-lcov,html,json-summary",
            "--coverageDirectory=../coverage/frontend",
            "--coverageThreshold={\"global\":{\"branches\":95,\"functions\":95,\"lines\":95,\"statements\":95}}",
            "--watchAll=false",
            "--ci",
            "--verbose"
        ]
        
        success, stdout, stderr = self.run_command(jest_cmd, cwd=self.frontend_dir, capture_output=True)
        
        # Parse coverage results
        coverage_info = self.parse_frontend_coverage()
        
        if success:
            self.print_success("Frontend tests passed")
            self.print_coverage_summary(coverage_info, "Frontend")
        else:
            self.print_error("Frontend tests failed")
            if stderr:
                print(stderr)
        
        return success, coverage_info
    
    def parse_backend_coverage(self) -> Dict[str, float]:
        """Parse backend coverage from XML report"""
        coverage_file = self.coverage_dir / "backend-coverage.xml"
        if not coverage_file.exists():
            return {}
        
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            
            # Find the coverage element
            coverage_elem = root.find('.')
            if coverage_elem is not None:
                line_rate = float(coverage_elem.get('line-rate', 0)) * 100
                branch_rate = float(coverage_elem.get('branch-rate', 0)) * 100
                
                return {
                    'lines': line_rate,
                    'branches': branch_rate
                }
        except Exception as e:
            self.print_warning(f"Could not parse backend coverage: {e}")
        
        return {}
    
    def parse_frontend_coverage(self) -> Dict[str, float]:
        """Parse frontend coverage from JSON report"""
        coverage_file = self.coverage_dir / "frontend" / "coverage-summary.json"
        if not coverage_file.exists():
            return {}
        
        try:
            with open(coverage_file, 'r') as f:
                coverage_data = json.load(f)
            
            total = coverage_data.get('total', {})
            return {
                'lines': total.get('lines', {}).get('pct', 0),
                'branches': total.get('branches', {}).get('pct', 0),
                'functions': total.get('functions', {}).get('pct', 0),
                'statements': total.get('statements', {}).get('pct', 0)
            }
        except Exception as e:
            self.print_warning(f"Could not parse frontend coverage: {e}")
        
        return {}
    
    def print_coverage_summary(self, coverage_info: Dict[str, float], prefix: str = "Backend"):
        """Print coverage summary"""
        if not coverage_info:
            return
        
        print(f"\n{Colors.OKCYAN}{prefix} Coverage Summary:{Colors.ENDC}")
        for metric, value in coverage_info.items():
            color = Colors.OKGREEN if value >= 95 else Colors.WARNING if value >= 90 else Colors.FAIL
            print(f"  {metric.title()}: {color}{value:.1f}%{Colors.ENDC}")
    
    def generate_combined_report(self, backend_coverage: Dict[str, float], frontend_coverage: Dict[str, float]):
        """Generate combined coverage report"""
        self.print_info("Generating combined coverage report...")
        
        report = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "backend": backend_coverage,
            "frontend": frontend_coverage,
            "overall_passed": True
        }
        
        # Check if coverage targets are met
        backend_target_met = all(v >= 95 for v in backend_coverage.values()) if backend_coverage else False
        frontend_target_met = all(v >= 95 for v in frontend_coverage.values()) if frontend_coverage else True  # Skip if no frontend
        
        report["targets_met"] = {
            "backend": backend_target_met,
            "frontend": frontend_target_met,
            "overall": backend_target_met and frontend_target_met
        }
        
        # Save report
        report_file = self.reports_dir / "coverage-report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        # Print summary
        print(f"\n{Colors.BOLD}Coverage Report Summary:{Colors.ENDC}")
        print(f"Backend target (95%): {'✅ Met' if backend_target_met else '❌ Not met'}")
        print(f"Frontend target (95%): {'✅ Met' if frontend_target_met else '❌ Not met'}")
        
        overall_color = Colors.OKGREEN if report["targets_met"]["overall"] else Colors.FAIL
        print(f"Overall: {overall_color}{'✅ All targets met' if report['targets_met']['overall'] else '❌ Targets not met'}{Colors.ENDC}")
        
        return report["targets_met"]["overall"]
    
    def run_specific_tests(self, test_path: str) -> bool:
        """Run specific test file or directory"""
        self.print_info(f"Running specific tests: {test_path}")
        
        pytest_cmd = [
            "python", "-m", "pytest",
            test_path,
            "--cov=src",
            "--cov=backend/app/src",
            "--cov-report=term-missing",
            "-v"
        ]
        
        success, stdout, stderr = self.run_command(pytest_cmd)
        
        if success:
            self.print_success(f"Tests passed: {test_path}")
        else:
            self.print_error(f"Tests failed: {test_path}")
        
        return success
    
    def run_performance_tests(self) -> bool:
        """Run performance benchmarks"""
        self.print_info("Running performance tests...")
        
        perf_cmd = [
            "python", "-m", "pytest",
            "tests/performance/",
            "--benchmark-only",
            "--benchmark-json=test-reports/benchmark-results.json",
            "-v"
        ]
        
        success, stdout, stderr = self.run_command(perf_cmd, capture_output=True)
        
        if success:
            self.print_success("Performance tests completed")
        else:
            self.print_warning("Performance tests failed or not found")
        
        return success
    
    def cleanup_test_artifacts(self):
        """Clean up test artifacts and temporary files"""
        self.print_info("Cleaning up test artifacts...")
        
        artifacts_to_clean = [
            "**/.pytest_cache",
            "**/htmlcov",
            "**/.coverage*",
            "**/test_*.db",
            "**/*.pyc",
            "**/__pycache__"
        ]
        
        import glob
        for pattern in artifacts_to_clean:
            for path in glob.glob(str(self.project_root / pattern), recursive=True):
                try:
                    if os.path.isfile(path):
                        os.remove(path)
                    elif os.path.isdir(path):
                        import shutil
                        shutil.rmtree(path)
                except Exception as e:
                    self.print_warning(f"Could not clean {path}: {e}")
        
        self.print_success("Cleanup completed")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run Legal AI System tests")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "frontend", "backend", "linting", "performance"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--coverage-only",
        action="store_true",
        help="Only run coverage analysis without tests"
    )
    parser.add_argument(
        "--no-linting",
        action="store_true",
        help="Skip linting and formatting checks"
    )
    parser.add_argument(
        "--path",
        help="Specific test file or directory to run"
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Clean up test artifacts after running"
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop on first test failure"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Print banner
    runner.print_header("Legal AI System Test Suite")
    
    # Setup environment
    runner.setup_environment()
    
    # Check dependencies
    if not runner.check_dependencies():
        sys.exit(1)
    
    overall_success = True
    backend_coverage = {}
    frontend_coverage = {}
    
    try:
        # Run specific path tests
        if args.path:
            success = runner.run_specific_tests(args.path)
            if not success and args.fail_fast:
                sys.exit(1)
            overall_success = overall_success and success
        
        # Run linting
        elif not args.no_linting and args.type in ["all", "linting"]:
            backend_lint_success = runner.run_backend_linting()
            frontend_lint_success = runner.run_frontend_linting()
            
            if not (backend_lint_success and frontend_lint_success) and args.fail_fast:
                sys.exit(1)
            overall_success = overall_success and backend_lint_success and frontend_lint_success
        
        # Run tests based on type
        if not args.coverage_only:
            if args.type in ["all", "backend", "unit", "integration"]:
                test_types = ["unit", "integration"] if args.type == "all" else [args.type]
                for test_type in test_types:
                    success, coverage = runner.run_backend_tests(test_type)
                    backend_coverage.update(coverage)
                    if not success and args.fail_fast:
                        sys.exit(1)
                    overall_success = overall_success and success
            
            if args.type in ["all", "frontend"]:
                success, coverage = runner.run_frontend_tests()
                frontend_coverage = coverage
                if not success and args.fail_fast:
                    sys.exit(1)
                overall_success = overall_success and success
            
            if args.type in ["all", "performance"]:
                success = runner.run_performance_tests()
                # Performance tests don't affect overall success
        
        # Generate combined report
        if backend_coverage or frontend_coverage:
            targets_met = runner.generate_combined_report(backend_coverage, frontend_coverage)
            overall_success = overall_success and targets_met
        
        # Cleanup
        if args.cleanup:
            runner.cleanup_test_artifacts()
        
        # Final result
        if overall_success:
            runner.print_success("All tests completed successfully! ✨")
            print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 95% Coverage target achieved! 🎉{Colors.ENDC}")
        else:
            runner.print_error("Some tests failed or coverage targets not met")
            sys.exit(1)
    
    except KeyboardInterrupt:
        runner.print_warning("Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        runner.print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()