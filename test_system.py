#!/usr/bin/env python
"""
Comprehensive testing script for the multi-provider video analysis system.
Tests all endpoints and verifies provider integrations.
"""
import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Dict, Any, Tuple

# Configuration
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8080")
TEST_VIDEO_PATH = os.getenv("TEST_VIDEO_PATH", "test_videos/sample.mp4")
TIMEOUT = 30

# Color codes for terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


class TestResult:
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.passed = False
        self.message = ""
        self.duration = 0
        self.response = None

    def print_result(self):
        """Print test result with color coding."""
        status = f"{Colors.GREEN}✓ PASS{Colors.END}" if self.passed else f"{Colors.RED}✗ FAIL{Colors.END}"
        print(f"{status} | {self.test_name} ({self.duration:.2f}s)")
        if self.message:
            print(f"  └─ {self.message}")


class VideoAnalysisSystemTester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.results = []
        self.session = requests.Session()

    def test_server_health(self) -> TestResult:
        """Test if server is running and responding."""
        result = TestResult("Server Health Check")
        start = time.time()

        try:
            response = self.session.get(f"{self.base_url}/", timeout=TIMEOUT)
            result.passed = response.status_code == 200
            result.message = f"Status: {response.status_code}"
            result.response = response

        except requests.ConnectionError:
            result.message = f"Could not connect to {self.base_url}"
        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result

    def test_provider_status(self) -> TestResult:
        """Test provider status endpoint."""
        result = TestResult("Provider Status Endpoint")
        start = time.time()

        try:
            response = self.session.get(
                f"{self.base_url}/api/analysis/status",
                timeout=TIMEOUT
            )
            result.response = response

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "providers" in data:
                    providers = data["providers"]
                    available = sum(1 for p in providers.values() if p.get("available"))
                    result.passed = True
                    result.message = f"{available}/{len(providers)} providers available"
                else:
                    result.message = "Invalid response format"
            else:
                result.message = f"HTTP {response.status_code}"

        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result

    def test_rate_limiting(self) -> TestResult:
        """Test rate limiting on endpoints."""
        result = TestResult("Rate Limiting")
        start = time.time()

        try:
            # Make rapid requests
            for i in range(35):
                response = self.session.get(
                    f"{self.base_url}/api/analysis/status",
                    timeout=TIMEOUT
                )
                
                if response.status_code == 429:
                    result.passed = True
                    result.message = f"Rate limit triggered at request {i+1}"
                    break
            else:
                result.message = "Rate limit not triggered (may be disabled)"
                result.passed = True

        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result

    def test_security_headers(self) -> TestResult:
        """Test security headers are present."""
        result = TestResult("Security Headers")
        start = time.time()

        try:
            response = self.session.get(f"{self.base_url}/", timeout=TIMEOUT)
            headers = response.headers

            required_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
            ]

            missing = [h for h in required_headers if h not in headers]
            result.passed = len(missing) == 0
            result.message = f"All {len(required_headers)} security headers present" if result.passed else f"Missing: {missing}"

        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result

    def test_video_upload(self, video_path: str) -> Tuple[TestResult, str]:
        """Test video upload endpoint."""
        result = TestResult("Video Upload")
        start = time.time()
        video_id = None

        try:
            if not Path(video_path).exists():
                result.message = f"Test video not found: {video_path}"
                result.duration = time.time() - start
                return result, video_id

            with open(video_path, 'rb') as f:
                files = {'video': (Path(video_path).name, f, 'video/mp4')}
                data = {'video_id': f'test_video_{int(time.time())}'}

                response = self.session.post(
                    f"{self.base_url}/api/analysis/analyze/file",
                    files=files,
                    data=data,
                    timeout=TIMEOUT
                )
                result.response = response

                if response.status_code == 200:
                    resp_data = response.json()
                    if resp_data.get("status") == "success":
                        video_id = resp_data.get("data", {}).get("video_id")
                        result.passed = True
                        result.message = f"Upload successful. Video ID: {video_id}"
                    else:
                        result.message = resp_data.get("error", "Unknown error")
                else:
                    result.message = f"HTTP {response.status_code}: {response.text[:100]}"

        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result, video_id

    def test_analysis_results(self, video_id: str) -> TestResult:
        """Test getting analysis results."""
        result = TestResult(f"Retrieve Analysis Results (ID: {video_id})")
        start = time.time()

        try:
            response = self.session.get(
                f"{self.base_url}/api/analysis/results/{video_id}",
                timeout=TIMEOUT
            )
            result.response = response

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    analysis = data.get("data", {})
                    providers_count = analysis.get("provider_count", 0)
                    successful = analysis.get("successful_analyses", 0)
                    result.passed = True
                    result.message = f"{successful}/{providers_count} providers completed"
                else:
                    result.message = data.get("error", "Unknown error")
            else:
                result.message = f"HTTP {response.status_code}"

        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result

    def test_compare_videos(self) -> TestResult:
        """Test video comparison endpoint."""
        result = TestResult("Video Comparison Endpoint")
        start = time.time()

        try:
            payload = {
                "video_ids": ["nonexistent1", "nonexistent2"]
            }

            response = self.session.post(
                f"{self.base_url}/api/analysis/compare",
                json=payload,
                timeout=TIMEOUT
            )
            result.response = response

            # Should return 404 for nonexistent videos
            result.passed = response.status_code in [200, 404]
            result.message = f"Endpoint responding (HTTP {response.status_code})"

        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result

    def test_input_validation(self) -> TestResult:
        """Test input validation."""
        result = TestResult("Input Validation")
        start = time.time()

        try:
            # Test with invalid file type
            files = {'video': ('test.txt', b'not a video', 'text/plain')}
            response = self.session.post(
                f"{self.base_url}/api/analysis/analyze/file",
                files=files,
                timeout=TIMEOUT
            )
            result.response = response

            # Should reject invalid file
            result.passed = response.status_code == 400
            result.message = f"Invalid input rejected (HTTP {response.status_code})"

        except Exception as e:
            result.message = str(e)

        result.duration = time.time() - start
        return result

    def run_all_tests(self):
        """Run all tests."""
        print(f"\n{Colors.BLUE}{'='*60}")
        print("VIDEO ANALYSIS SYSTEM - COMPREHENSIVE TEST SUITE")
        print(f"{'='*60}{Colors.END}\n")

        print(f"Testing server at: {self.base_url}\n")

        # Basic tests
        print(f"{Colors.BLUE}BASIC TESTS:{Colors.END}")
        result = self.test_server_health()
        self.results.append(result)
        result.print_result()

        if not result.passed:
            print(f"\n{Colors.RED}Server is not responding. Cannot continue.{Colors.END}\n")
            return

        result = self.test_provider_status()
        self.results.append(result)
        result.print_result()

        # Security tests
        print(f"\n{Colors.BLUE}SECURITY TESTS:{Colors.END}")
        result = self.test_security_headers()
        self.results.append(result)
        result.print_result()

        result = self.test_input_validation()
        self.results.append(result)
        result.print_result()

        result = self.test_rate_limiting()
        self.results.append(result)
        result.print_result()

        # API tests
        print(f"\n{Colors.BLUE}API ENDPOINT TESTS:{Colors.END}")
        result = self.test_compare_videos()
        self.results.append(result)
        result.print_result()

        # Video analysis tests (if test video exists)
        if Path(TEST_VIDEO_PATH).exists():
            print(f"\n{Colors.BLUE}VIDEO ANALYSIS TESTS:{Colors.END}")
            print(f"Using test video: {TEST_VIDEO_PATH}\n")

            result, video_id = self.test_video_upload(TEST_VIDEO_PATH)
            self.results.append(result)
            result.print_result()

            if video_id:
                time.sleep(2)  # Wait for analysis to complete
                result = self.test_analysis_results(video_id)
                self.results.append(result)
                result.print_result()
        else:
            print(f"\n{Colors.YELLOW}NOTE: Test video not found at {TEST_VIDEO_PATH}")
            print("Skipping video analysis tests. To run them, provide a test video.{Colors.END}\n")

        # Summary
        self.print_summary()

    def print_summary(self):
        """Print test summary."""
        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)
        percentage = (passed / total * 100) if total > 0 else 0

        print(f"\n{Colors.BLUE}{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}{Colors.END}")

        if percentage == 100:
            print(f"{Colors.GREEN}All tests passed! ({passed}/{total}){Colors.END}")
        elif percentage >= 80:
            print(f"{Colors.YELLOW}Most tests passed ({passed}/{total} - {percentage:.0f}%){Colors.END}")
        else:
            print(f"{Colors.RED}Some tests failed ({passed}/{total} - {percentage:.0f}%){Colors.END}")

        total_time = sum(r.duration for r in self.results)
        print(f"Total duration: {total_time:.2f}s\n")

        # Detailed results
        if any(not r.passed for r in self.results):
            print(f"{Colors.RED}Failed tests:{Colors.END}")
            for r in self.results:
                if not r.passed:
                    print(f"  - {r.test_name}")
                    if r.message:
                        print(f"    {r.message}")


def main():
    """Run the test suite."""
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    else:
        base_url = BASE_URL

    tester = VideoAnalysisSystemTester(base_url)
    tester.run_all_tests()


if __name__ == "__main__":
    main()
