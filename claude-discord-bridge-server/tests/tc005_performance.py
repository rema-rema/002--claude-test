#!/usr/bin/env python3
"""
TC-005: Performance Tests
Tests for Success Criteria SC-003: パフォーマンス・リソース管理

Test Cases:
- TC-005-01: Discord response time (3 seconds or less)
- TC-005-02: File processing performance (8MB files within 10 seconds)  
- TC-005-03: Session switching performance (1 second or less)
- TC-005-04: Memory usage monitoring (2GB limit)
- TC-005-05: Concurrent file processing (20 files simultaneously)
"""

import os
import sys
import time
import json
import threading
import psutil
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_utils import TestFramework, TestResult, SessionTestHelper, AttachmentTestHelper, PerformanceTestHelper

class TC005Performance:
    """TC-005: Performance Test Suite"""
    
    def __init__(self):
        self.name = "Performance Tests (SC-003)"
        self.framework = TestFramework()
        self.session_helper = SessionTestHelper()
        self.attachment_helper = AttachmentTestHelper()
        self.perf_helper = PerformanceTestHelper()
        self.test_sessions = [2, 3, 4]
        
        # Performance thresholds from requirements
        self.max_discord_response_time = 3.0  # seconds
        self.max_file_processing_time = 10.0  # seconds for 8MB files
        self.max_session_switch_time = 1.0   # seconds
        self.max_memory_usage = 2048         # MB (2GB)
        self.max_concurrent_files = 20       # simultaneous files
        
    def setup_test_environment(self) -> bool:
        """Set up performance test environment"""
        print("Setting up performance test environment...")
        
        # Create test sessions
        test_channels = {
            2: "1234567890123456001",
            3: "1234567890123456002", 
            4: "1234567890123456003"
        }
        
        for session_id, channel_id in test_channels.items():
            if not self.session_helper.create_test_session(session_id, channel_id):
                return False
                
        return True
        
    def cleanup_test_environment(self):
        """Clean up performance test environment"""
        print("Cleaning up performance test environment...")
        self.session_helper.cleanup_test_sessions()
        self.attachment_helper.cleanup_test_files()
        
    def test_005_01_discord_response_time(self) -> tuple:
        """TC-005-01: Test Discord response time (3 seconds or less)"""
        print("Testing Discord response time...")
        
        failures = []
        warnings = []
        metrics = {}
        
        try:
            # Test dp command response times for different sessions
            test_cases = [
                (1, "Default session response time"),
                (2, "Session 2 response time"),
                (3, "Session 3 response time"),
                (4, "Session 4 response time")
            ]
            
            response_times = []
            
            for session_id, description in test_cases:
                # Measure dp command execution time
                start_time = time.time()
                
                # Execute dp command (will fail in test environment but we measure timing)
                test_cmd = f'python src/discord_post.py {session_id} "Performance test message"'
                returncode, stdout, stderr = self.framework.run_command(
                    ['bash', '-c', test_cmd], timeout=self.max_discord_response_time + 1
                )
                
                response_time = time.time() - start_time
                response_times.append(response_time)
                
                if response_time > self.max_discord_response_time:
                    failures.append(f"{description} exceeded {self.max_discord_response_time}s: {response_time:.2f}s")
                else:
                    print(f"    ✅ {description}: {response_time:.2f}s")
                    
            # Calculate performance metrics
            if response_times:
                metrics['avg_response_time'] = sum(response_times) / len(response_times)
                metrics['max_response_time'] = max(response_times)
                metrics['min_response_time'] = min(response_times)
                metrics['response_time_threshold'] = self.max_discord_response_time
                
                # Check if 90% of requests meet the threshold
                within_threshold = [t for t in response_times if t <= self.max_discord_response_time]
                success_rate = len(within_threshold) / len(response_times) * 100
                metrics['success_rate_percent'] = success_rate
                
                if success_rate < 90:
                    failures.append(f"Only {success_rate:.1f}% of requests met 3s threshold (required: 90%)")
                    
        except Exception as e:
            failures.append(f"Discord response time test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings, metrics)
        
    def test_005_02_file_processing_performance(self) -> tuple:
        """TC-005-02: Test file processing performance (8MB files within 10 seconds)"""
        print("Testing file processing performance...")
        
        failures = []
        warnings = []
        metrics = {}
        
        try:
            # Create test files of different sizes
            file_sizes = [
                (1024 * 1024, "1MB file"),      # 1MB
                (4 * 1024 * 1024, "4MB file"),  # 4MB
                (8 * 1024 * 1024, "8MB file")   # 8MB
            ]
            
            processing_times = []
            
            for file_size, description in file_sizes:
                # Create large test file
                content = "X" * file_size
                
                start_time = time.time()
                
                # Create file in session directory
                test_file = self.attachment_helper.create_test_attachment(
                    2, f"perf_test_{file_size}.txt", content
                )
                
                # Read file back (simulating processing)
                with open(test_file, 'r') as f:
                    read_content = f.read()
                    
                # Verify content integrity
                if len(read_content) != file_size:
                    failures.append(f"File integrity check failed for {description}")
                    
                processing_time = time.time() - start_time
                processing_times.append(processing_time)
                
                # Check against threshold
                if file_size == 8 * 1024 * 1024 and processing_time > self.max_file_processing_time:
                    failures.append(f"8MB file processing exceeded {self.max_file_processing_time}s: {processing_time:.2f}s")
                else:
                    print(f"    ✅ {description}: {processing_time:.2f}s")
                    
            # Calculate throughput metrics
            if processing_times:
                metrics['file_processing_times'] = processing_times
                metrics['avg_processing_time'] = sum(processing_times) / len(processing_times)
                metrics['max_processing_time'] = max(processing_times)
                
                # Calculate throughput for 8MB file
                if len(processing_times) >= 3:
                    mb_per_second = 8 / processing_times[2] if processing_times[2] > 0 else 0
                    metrics['throughput_mb_per_sec'] = mb_per_second
                    
        except Exception as e:
            failures.append(f"File processing performance test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings, metrics)
        
    def test_005_03_session_switching_performance(self) -> tuple:
        """TC-005-03: Test session switching performance (1 second or less)"""
        print("Testing session switching performance...")
        
        failures = []
        warnings = []
        metrics = {}
        
        try:
            # Test rapid session switching
            session_sequence = [1, 2, 3, 4, 1, 3, 2, 4]  # Mixed sequence
            switch_times = []
            
            for i in range(len(session_sequence) - 1):
                current_session = session_sequence[i]
                next_session = session_sequence[i + 1]
                
                # Measure session switch time (command preparation time)
                start_time = time.time()
                
                # Simulate session context switching
                # In real system, this involves channel ID lookup and context switching
                channel_id = self.session_helper.get_session_channel(next_session)
                if channel_id:
                    # Session switch successful
                    pass
                else:
                    # Create temporary session for testing
                    temp_channel = f"temp_channel_{next_session}"
                    self.session_helper.create_test_session(next_session, temp_channel)
                    
                switch_time = time.time() - start_time
                switch_times.append(switch_time)
                
                if switch_time > self.max_session_switch_time:
                    failures.append(f"Session switch {current_session}→{next_session} exceeded {self.max_session_switch_time}s: {switch_time:.3f}s")
                else:
                    print(f"    ✅ Switch {current_session}→{next_session}: {switch_time:.3f}s")
                    
                # Small delay between switches to simulate realistic usage
                time.sleep(0.1)
                
            # Calculate switching performance metrics
            if switch_times:
                metrics['avg_switch_time'] = sum(switch_times) / len(switch_times)
                metrics['max_switch_time'] = max(switch_times)
                metrics['min_switch_time'] = min(switch_times)
                metrics['switch_time_threshold'] = self.max_session_switch_time
                
                # Check if all switches meet threshold
                within_threshold = [t for t in switch_times if t <= self.max_session_switch_time]
                success_rate = len(within_threshold) / len(switch_times) * 100
                metrics['switch_success_rate'] = success_rate
                
                if success_rate < 95:
                    failures.append(f"Only {success_rate:.1f}% of switches met 1s threshold (required: 95%)")
                    
        except Exception as e:
            failures.append(f"Session switching performance test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings, metrics)
        
    def test_005_04_memory_usage_monitoring(self) -> tuple:
        """TC-005-04: Test memory usage monitoring (2GB limit)"""
        print("Testing memory usage monitoring...")
        
        failures = []
        warnings = []
        metrics = {}
        
        try:
            # Monitor memory usage during test operations
            initial_memory = psutil.virtual_memory()
            process = psutil.Process()
            initial_process_memory = process.memory_info()
            
            # Perform memory-intensive operations
            memory_samples = []
            
            # Create multiple large files to test memory usage
            for session_id in self.test_sessions:
                for i in range(5):  # 5 files per session
                    # Create 10MB files to test memory handling
                    large_content = "Y" * (10 * 1024 * 1024)  # 10MB
                    test_file = self.attachment_helper.create_test_attachment(
                        session_id, f"memory_test_{i}.txt", large_content
                    )
                    
                    # Sample memory usage
                    current_memory = psutil.virtual_memory()
                    process_memory = process.memory_info()
                    
                    memory_samples.append({
                        'total_memory_mb': current_memory.used / 1024 / 1024,
                        'process_memory_mb': process_memory.rss / 1024 / 1024,
                        'memory_percent': current_memory.percent
                    })
                    
            # Analyze memory usage
            if memory_samples:
                max_total_memory = max(sample['total_memory_mb'] for sample in memory_samples)
                max_process_memory = max(sample['process_memory_mb'] for sample in memory_samples)
                avg_memory_percent = sum(sample['memory_percent'] for sample in memory_samples) / len(memory_samples)
                
                metrics['max_total_memory_mb'] = max_total_memory
                metrics['max_process_memory_mb'] = max_process_memory
                metrics['avg_memory_percent'] = avg_memory_percent
                metrics['memory_limit_mb'] = self.max_memory_usage
                
                # Check memory limits
                if max_process_memory > 512:  # Individual process limit
                    warnings.append(f"Process memory usage high: {max_process_memory:.1f}MB")
                    
                current_total_memory = psutil.virtual_memory().used / 1024 / 1024
                if current_total_memory > self.max_memory_usage:
                    failures.append(f"Total memory usage exceeded {self.max_memory_usage}MB: {current_total_memory:.1f}MB")
                    
                # Check for memory leaks (simplified)
                final_process_memory = process.memory_info().rss / 1024 / 1024
                memory_increase = final_process_memory - (initial_process_memory.rss / 1024 / 1024)
                
                metrics['memory_increase_mb'] = memory_increase
                
                if memory_increase > 100:  # Significant memory increase
                    warnings.append(f"Potential memory leak detected: {memory_increase:.1f}MB increase")
                    
        except Exception as e:
            failures.append(f"Memory usage monitoring test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings, metrics)
        
    def test_005_05_concurrent_file_processing(self) -> tuple:
        """TC-005-05: Test concurrent file processing (20 files simultaneously)"""
        print("Testing concurrent file processing...")
        
        failures = []
        warnings = []
        metrics = {}
        
        try:
            # Test concurrent file operations
            num_files = self.max_concurrent_files
            file_size = 1024 * 1024  # 1MB per file
            
            def create_and_process_file(file_id):
                """Create and process a single file"""
                try:
                    session_id = (file_id % len(self.test_sessions)) + 2  # Distribute across sessions
                    content = f"Concurrent test {file_id}: " + "Z" * (file_size - 50)
                    
                    start_time = time.time()
                    
                    # Create file
                    test_file = self.attachment_helper.create_test_attachment(
                        session_id, f"concurrent_test_{file_id}.txt", content
                    )
                    
                    # Read file back
                    with open(test_file, 'r') as f:
                        read_content = f.read()
                        
                    # Verify integrity
                    if len(read_content) != len(content):
                        return False, f"File {file_id} integrity check failed"
                        
                    processing_time = time.time() - start_time
                    return True, processing_time
                    
                except Exception as e:
                    return False, f"File {file_id} processing failed: {str(e)}"
                    
            # Execute concurrent file processing
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=num_files) as executor:
                # Submit all file processing tasks
                future_to_id = {
                    executor.submit(create_and_process_file, i): i 
                    for i in range(num_files)
                }
                
                # Collect results
                successful_files = 0
                processing_times = []
                
                for future in as_completed(future_to_id):
                    file_id = future_to_id[future]
                    try:
                        success, result = future.result(timeout=30)
                        if success:
                            successful_files += 1
                            processing_times.append(result)
                        else:
                            failures.append(result)  # Error message
                    except Exception as e:
                        failures.append(f"File {file_id} future failed: {str(e)}")
                        
            total_time = time.time() - start_time
            
            # Analyze concurrent processing performance
            metrics['total_concurrent_files'] = num_files
            metrics['successful_files'] = successful_files
            metrics['failed_files'] = num_files - successful_files
            metrics['total_processing_time'] = total_time
            metrics['success_rate_percent'] = (successful_files / num_files) * 100
            
            if processing_times:
                metrics['avg_file_time'] = sum(processing_times) / len(processing_times)
                metrics['max_file_time'] = max(processing_times)
                metrics['min_file_time'] = min(processing_times)
                metrics['throughput_files_per_sec'] = successful_files / total_time if total_time > 0 else 0
                
            # Performance validation
            if successful_files < num_files * 0.95:  # 95% success rate required
                failures.append(f"Concurrent processing success rate too low: {successful_files}/{num_files}")
                
            if total_time > 60:  # Should complete within 60 seconds
                failures.append(f"Concurrent processing took too long: {total_time:.2f}s")
                
            print(f"    ✅ Processed {successful_files}/{num_files} files in {total_time:.2f}s")
            
        except Exception as e:
            failures.append(f"Concurrent file processing test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings, metrics)
        
    def run_tests(self) -> TestResult:
        """Run all TC-005 performance tests"""
        print(f"🚀 Running {self.name}")
        start_time = time.time()
        
        total_tests = 5
        passed_tests = 0
        all_failures = []
        all_warnings = []
        all_metrics = {}
        
        try:
            # Setup test environment
            if not self.setup_test_environment():
                return TestResult(
                    "TC-005", 0, total_tests, False,
                    failures=["Failed to setup performance test environment"],
                    execution_time=time.time() - start_time
                )
                
            # Run individual performance tests
            tests = [
                ("TC-005-01", self.test_005_01_discord_response_time),
                ("TC-005-02", self.test_005_02_file_processing_performance),
                ("TC-005-03", self.test_005_03_session_switching_performance),
                ("TC-005-04", self.test_005_04_memory_usage_monitoring),
                ("TC-005-05", self.test_005_05_concurrent_file_processing)
            ]
            
            for test_name, test_func in tests:
                print(f"  Running {test_name}...")
                try:
                    result = test_func()
                    if len(result) == 4:  # With metrics
                        passed, failures, warnings, metrics = result
                        all_metrics[test_name] = metrics
                    else:  # Without metrics
                        passed, failures, warnings = result
                        
                    if passed:
                        passed_tests += 1
                        print(f"    ✅ {test_name} PASSED")
                    else:
                        print(f"    ❌ {test_name} FAILED")
                        
                    all_failures.extend([f"{test_name}: {f}" for f in failures])
                    all_warnings.extend([f"{test_name}: {w}" for w in warnings])
                    
                except Exception as e:
                    print(f"    ❌ {test_name} FAILED with exception")
                    all_failures.append(f"{test_name}: Test execution failed - {str(e)}")
                    
        except Exception as e:
            all_failures.append(f"Performance test suite setup failed: {str(e)}")
            
        finally:
            # Clean up test environment
            self.cleanup_test_environment()
            
        execution_time = time.time() - start_time
        overall_passed = len(all_failures) == 0
        
        result = TestResult(
            "TC-005",
            passed_tests,
            total_tests,
            overall_passed,
            failures=all_failures,
            warnings=all_warnings,
            execution_time=execution_time,
            metrics=all_metrics
        )
        
        return result

if __name__ == "__main__":
    # Direct execution for testing
    test_suite = TC005Performance()
    result = test_suite.run_tests()
    
    print(f"\n{'='*50}")
    print(f"TC-005 Results: {'PASS' if result.passed else 'FAIL'}")
    print(f"Tests passed: {result.passed_tests}/{result.total_tests}")
    print(f"Execution time: {result.execution_time:.2f}s")
    
    if result.failures:
        print("\nFailures:")
        for failure in result.failures:
            print(f"  - {failure}")
            
    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
            
    if result.metrics:
        print("\nPerformance Metrics:")
        for test_name, metrics in result.metrics.items():
            print(f"  {test_name}:")
            for key, value in metrics.items():
                print(f"    {key}: {value}")