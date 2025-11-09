#!/usr/bin/env python3
"""
Comprehensive Test Runner for Torrent Downloader
Runs all test suites and provides detailed reporting
"""

import unittest
import sys
import os
import time
from io import StringIO

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class ColoredTextTestResult(unittest.TextTestResult):
    """Custom test result with colored output"""

    # ANSI color codes
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_times = {}
        self.current_test = None
        self.current_start_time = None

    def startTest(self, test):
        super().startTest(test)
        self.current_test = test
        self.current_start_time = time.time()

    def stopTest(self, test):
        super().stopTest(test)
        elapsed = time.time() - self.current_start_time
        self.test_times[test] = elapsed

    def addSuccess(self, test):
        super().addSuccess(test)
        elapsed = self.test_times.get(test, 0)
        self.stream.write(f"{self.GREEN}✓{self.RESET} ")
        self.stream.write(f"{test.id()} ")
        self.stream.write(f"({elapsed:.3f}s)\n")
        self.stream.flush()

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"{self.RED}✗{self.RESET} ")
        self.stream.write(f"{test.id()} - ERROR\n")
        self.stream.flush()

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"{self.RED}✗{self.RESET} ")
        self.stream.write(f"{test.id()} - FAILED\n")
        self.stream.flush()

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.stream.write(f"{self.YELLOW}⊘{self.RESET} ")
        self.stream.write(f"{test.id()} - SKIPPED: {reason}\n")
        self.stream.flush()


class TestSuite:
    """Main test suite runner"""

    def __init__(self):
        self.loader = unittest.TestLoader()
        self.suite = unittest.TestSuite()

    def discover_tests(self):
        """Discover all tests in the tests directory"""
        print("=" * 70)
        print("Torrent Downloader - Automated Test Suite")
        print("=" * 70)
        print()

        # Discover tests
        test_dir = os.path.join(os.path.dirname(__file__), 'tests')

        if not os.path.exists(test_dir):
            print(f"Error: Test directory not found: {test_dir}")
            return False

        print(f"Discovering tests in: {test_dir}")
        discovered_suite = self.loader.discover(test_dir, pattern='test_*.py')

        # Count tests
        test_count = discovered_suite.countTestCases()
        print(f"Found {test_count} tests")
        print()

        self.suite.addTests(discovered_suite)
        return True

    def run_tests(self, verbosity=2):
        """Run all discovered tests"""
        if self.suite.countTestCases() == 0:
            print("No tests to run!")
            return False

        print("=" * 70)
        print("Running Tests")
        print("=" * 70)
        print()

        # Run tests
        runner = unittest.TextTestRunner(
            verbosity=verbosity,
            resultclass=ColoredTextTestResult
        )

        start_time = time.time()
        result = runner.run(self.suite)
        elapsed_time = time.time() - start_time

        # Print summary
        self.print_summary(result, elapsed_time)

        return result.wasSuccessful()

    def print_summary(self, result, elapsed_time):
        """Print test summary"""
        print()
        print("=" * 70)
        print("Test Summary")
        print("=" * 70)
        print()

        total = result.testsRun
        passed = total - len(result.failures) - len(result.errors)
        failed = len(result.failures)
        errors = len(result.errors)
        skipped = len(result.skipped)

        # Overall status
        if result.wasSuccessful():
            status = f"\033[92m✓ ALL TESTS PASSED\033[0m"
        else:
            status = f"\033[91m✗ TESTS FAILED\033[0m"

        print(f"Status: {status}")
        print()
        print(f"Tests run:    {total}")
        print(f"  \033[92m✓ Passed:\033[0m   {passed}")
        if failed > 0:
            print(f"  \033[91m✗ Failed:\033[0m   {failed}")
        if errors > 0:
            print(f"  \033[91m✗ Errors:\033[0m   {errors}")
        if skipped > 0:
            print(f"  \033[93m⊘ Skipped:\033[0m  {skipped}")
        print()
        print(f"Time: {elapsed_time:.2f}s")
        print()

        # Show failures and errors
        if result.failures:
            print("=" * 70)
            print("Failures:")
            print("=" * 70)
            for test, traceback in result.failures:
                print(f"\n{test.id()}:")
                print(traceback)

        if result.errors:
            print("=" * 70)
            print("Errors:")
            print("=" * 70)
            for test, traceback in result.errors:
                print(f"\n{test.id()}:")
                print(traceback)

    def run_specific_suite(self, suite_name):
        """Run a specific test suite"""
        print(f"Running test suite: {suite_name}")
        print()

        test_file = f"tests.{suite_name}"
        try:
            suite = self.loader.loadTestsFromName(test_file)
            self.suite.addTests(suite)

            runner = unittest.TextTestRunner(
                verbosity=2,
                resultclass=ColoredTextTestResult
            )
            result = runner.run(self.suite)
            return result.wasSuccessful()
        except Exception as e:
            print(f"Error loading test suite: {e}")
            return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Run automated tests for Torrent Downloader'
    )
    parser.add_argument(
        '--suite',
        help='Run specific test suite (e.g., test_utils, test_validation)',
        default=None
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Minimal output'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available tests'
    )

    args = parser.parse_args()

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 2

    test_suite = TestSuite()

    # List tests
    if args.list:
        if test_suite.discover_tests():
            print("Available test suites:")
            test_dir = os.path.join(os.path.dirname(__file__), 'tests')
            for file in sorted(os.listdir(test_dir)):
                if file.startswith('test_') and file.endswith('.py'):
                    print(f"  - {file[:-3]}")
        return 0

    # Run specific suite
    if args.suite:
        success = test_suite.run_specific_suite(args.suite)
    else:
        # Run all tests
        if not test_suite.discover_tests():
            return 1
        success = test_suite.run_tests(verbosity=verbosity)

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
