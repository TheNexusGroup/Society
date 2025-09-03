#!/usr/bin/env python3
"""
Test runner script for Society simulation testing
"""

import sys
import os
import argparse
import subprocess
import time
import json
from pathlib import Path


class TestRunner:
    """Main test runner for Society simulation."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = None
    
    def run_unit_tests(self, verbose=False, coverage=True):
        """Run unit tests."""
        print("🧪 Running Unit Tests...")
        cmd = ["python", "-m", "pytest", "tests/unit/", "-v" if verbose else "-q"]
        
        if coverage:
            cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
        cmd.extend(["-m", "unit"])
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        self.test_results['unit'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
        if result.returncode == 0:
            print("✅ Unit tests passed")
        else:
            print("❌ Unit tests failed")
            if verbose:
                print(result.stdout)
                print(result.stderr)
        
        return result.returncode == 0
    
    def run_integration_tests(self, verbose=False):
        """Run integration tests."""
        print("🔗 Running Integration Tests...")
        cmd = ["python", "-m", "pytest", "tests/integration/", "-v" if verbose else "-q"]
        cmd.extend(["-m", "integration"])
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        self.test_results['integration'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
        if result.returncode == 0:
            print("✅ Integration tests passed")
        else:
            print("❌ Integration tests failed")
            if verbose:
                print(result.stdout)
                print(result.stderr)
        
        return result.returncode == 0
    
    def run_stress_tests(self, verbose=False):
        """Run stress tests."""
        print("💪 Running Stress Tests...")
        cmd = ["python", "-m", "pytest", "tests/stress/", "-v" if verbose else "-q"]
        cmd.extend(["-m", "stress", "--timeout=300"])
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        self.test_results['stress'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
        if result.returncode == 0:
            print("✅ Stress tests passed")
        else:
            print("❌ Stress tests failed")
            if verbose:
                print(result.stdout)
                print(result.stderr)
        
        return result.returncode == 0
    
    def run_benchmarks(self, verbose=False):
        """Run performance benchmarks."""
        print("⚡ Running Performance Benchmarks...")
        cmd = ["python", "-m", "pytest", "tests/benchmarks/", "-v" if verbose else "-q"]
        cmd.extend(["-m", "benchmark", "--benchmark-only", "--benchmark-sort=mean"])
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        self.test_results['benchmarks'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
        if result.returncode == 0:
            print("✅ Benchmarks completed")
        else:
            print("❌ Benchmarks failed")
            if verbose:
                print(result.stdout)
                print(result.stderr)
        
        return result.returncode == 0
    
    def run_critical_tests(self, verbose=False):
        """Run tests for critical issues."""
        print("🚨 Running Critical Issue Tests...")
        cmd = ["python", "-m", "pytest", "tests/unit/critical/", "-v" if verbose else "-q"]
        cmd.extend(["-m", "critical"])
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        self.test_results['critical'] = {
            'returncode': result.returncode,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'success': result.returncode == 0
        }
        
        if result.returncode == 0:
            print("✅ Critical tests passed")
        else:
            print("❌ Critical tests failed")
            if verbose:
                print(result.stdout)
                print(result.stderr)
        
        return result.returncode == 0
    
    def run_coverage_report(self):
        """Generate coverage report."""
        print("📊 Generating Coverage Report...")
        
        # Generate HTML coverage report
        cmd = ["python", "-m", "pytest", "--cov=src", "--cov-report=html:tests/coverage_html", 
               "--cov-report=xml:tests/coverage.xml", "--cov-report=term", "tests/"]
        
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Coverage report generated")
            print(f"📁 HTML report: {self.project_root}/tests/coverage_html/index.html")
        else:
            print("❌ Coverage report failed")
        
        return result.returncode == 0
    
    def install_test_dependencies(self):
        """Install test dependencies."""
        print("📦 Installing test dependencies...")
        
        cmd = ["pip", "install", "-r", "requirements-test.txt"]
        result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Test dependencies installed")
        else:
            print("❌ Failed to install test dependencies")
            print(result.stderr)
        
        return result.returncode == 0
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("📋 Generating Test Report...")
        
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_duration': time.time() - self.start_time if self.start_time else 0,
            'test_results': self.test_results,
            'summary': {
                'total_test_suites': len(self.test_results),
                'passed_suites': sum(1 for r in self.test_results.values() if r['success']),
                'failed_suites': sum(1 for r in self.test_results.values() if not r['success']),
                'overall_success': all(r['success'] for r in self.test_results.values())
            }
        }
        
        # Write JSON report
        report_file = self.project_root / "tests" / "test_report.json"
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # Generate markdown report
        self._generate_markdown_report(report_data)
        
        print(f"✅ Test report generated: {report_file}")
        return report_data
    
    def _generate_markdown_report(self, report_data):
        """Generate markdown test report."""
        report_file = self.project_root / "tests" / "TEST_REPORT.md"
        
        content = f"""# Society Simulation Test Report
        
**Generated**: {report_data['timestamp']}
**Duration**: {report_data['total_duration']:.2f} seconds
**Overall Status**: {'✅ PASSED' if report_data['summary']['overall_success'] else '❌ FAILED'}

## Summary
- **Total Test Suites**: {report_data['summary']['total_test_suites']}
- **Passed**: {report_data['summary']['passed_suites']}
- **Failed**: {report_data['summary']['failed_suites']}

## Test Suite Results

"""
        
        for suite_name, result in report_data['test_results'].items():
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            content += f"### {suite_name.title()} Tests\n"
            content += f"**Status**: {status}\n"
            content += f"**Return Code**: {result['returncode']}\n\n"
            
            if not result['success'] and result['stderr']:
                content += "**Error Output**:\n```\n"
                content += result['stderr'][:1000] + ("..." if len(result['stderr']) > 1000 else "")
                content += "\n```\n\n"
        
        content += """## Recommendations

Based on test results:

"""
        
        if not report_data['summary']['overall_success']:
            content += "- 🚨 **Action Required**: Some tests failed and need attention\n"
            content += "- 🔍 Review failed test output above\n"
            content += "- 🛠️ Fix issues before deploying changes\n"
        else:
            content += "- ✅ All tests passing - good to go!\n"
            content += "- 📊 Review coverage report for any gaps\n"
            content += "- ⚡ Check benchmark results for performance regressions\n"
        
        with open(report_file, 'w') as f:
            f.write(content)
    
    def run_all_tests(self, verbose=False, include_benchmarks=True, coverage=True):
        """Run all test suites."""
        self.start_time = time.time()
        
        print("🚀 Starting Society Simulation Test Suite")
        print("=" * 50)
        
        results = {
            'unit': self.run_unit_tests(verbose, coverage),
            'integration': self.run_integration_tests(verbose),
            'critical': self.run_critical_tests(verbose),
            'stress': self.run_stress_tests(verbose)
        }
        
        if include_benchmarks:
            results['benchmarks'] = self.run_benchmarks(verbose)
        
        if coverage:
            self.run_coverage_report()
        
        # Generate final report
        report = self.generate_test_report()
        
        print("=" * 50)
        if report['summary']['overall_success']:
            print("🎉 ALL TESTS PASSED!")
        else:
            print("💥 SOME TESTS FAILED!")
        
        print(f"⏱️  Total time: {report['total_duration']:.2f} seconds")
        print(f"📊 Test suites: {report['summary']['passed_suites']}/{report['summary']['total_test_suites']} passed")
        
        return report['summary']['overall_success']


def main():
    """Main entry point for test runner."""
    parser = argparse.ArgumentParser(description="Society Simulation Test Runner")
    
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--stress', action='store_true', help='Run stress tests only')
    parser.add_argument('--benchmarks', action='store_true', help='Run benchmarks only')
    parser.add_argument('--critical', action='store_true', help='Run critical issue tests only')
    parser.add_argument('--coverage', action='store_true', help='Generate coverage report')
    parser.add_argument('--install', action='store_true', help='Install test dependencies')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--no-benchmarks', action='store_true', help='Skip benchmarks in full run')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Handle dependency installation
    if args.install:
        if not runner.install_test_dependencies():
            sys.exit(1)
        return
    
    # Handle specific test suite runs
    if args.unit:
        success = runner.run_unit_tests(args.verbose, coverage=True)
        sys.exit(0 if success else 1)
    
    if args.integration:
        success = runner.run_integration_tests(args.verbose)
        sys.exit(0 if success else 1)
    
    if args.stress:
        success = runner.run_stress_tests(args.verbose)
        sys.exit(0 if success else 1)
    
    if args.benchmarks:
        success = runner.run_benchmarks(args.verbose)
        sys.exit(0 if success else 1)
    
    if args.critical:
        success = runner.run_critical_tests(args.verbose)
        sys.exit(0 if success else 1)
    
    if args.coverage:
        success = runner.run_coverage_report()
        sys.exit(0 if success else 1)
    
    # Run all tests by default
    success = runner.run_all_tests(
        verbose=args.verbose,
        include_benchmarks=not args.no_benchmarks,
        coverage=True
    )
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()