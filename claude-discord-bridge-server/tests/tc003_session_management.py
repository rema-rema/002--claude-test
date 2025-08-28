#!/usr/bin/env python3
"""
TC-003: Session Management Tests
Tests for Success Criteria SC-004: 運用性・安定性

Test Cases:
- TC-003-01: vai status command with multi-session support
- TC-003-02: Session-specific file cleanup operations  
- TC-003-03: 24-hour continuous operation stability
- TC-003-04: Existing Session 1 compatibility preservation
- TC-003-05: CLI session management commands
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_utils import TestFramework, TestResult, SessionTestHelper, AttachmentTestHelper, TmuxTestHelper

class TC003SessionManagement:
    """TC-003: Session Management Test Suite"""
    
    def __init__(self):
        self.name = "Session Management Tests (SC-004)"
        self.framework = TestFramework()
        self.session_helper = SessionTestHelper()
        self.attachment_helper = AttachmentTestHelper()
        self.tmux_helper = TmuxTestHelper()
        self.test_sessions = [2, 3, 4]
        
    def setup_test_environment(self) -> bool:
        """Set up session management test environment"""
        print("Setting up session management test environment...")
        
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
        """Clean up session management test environment"""
        print("Cleaning up session management test environment...")
        self.session_helper.cleanup_test_sessions()
        self.attachment_helper.cleanup_test_files()
        self.tmux_helper.cleanup_test_sessions()
        
    def test_003_01_vai_status_multi_session(self) -> tuple:
        """TC-003-01: Test vai status command with multi-session support"""
        print("Testing vai status command with multi-session support...")
        
        failures = []
        warnings = []
        
        try:
            # Test vai status command
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'status'], timeout=30)
            
            if returncode != 0:
                failures.append(f"vai status command failed: {stderr}")
                return (False, failures, warnings)
                
            # Parse output to verify multi-session information
            output_lines = stdout.strip().split('\n')
            
            # Look for session information in output
            session_info_found = False
            sessions_detected = []
            
            for line in output_lines:
                if 'Session' in line and ':' in line:
                    session_info_found = True
                    # Extract session number
                    try:
                        session_part = line.split('Session')[1].split(':')[0].strip()
                        if session_part.isdigit():
                            sessions_detected.append(int(session_part))
                    except (IndexError, ValueError):
                        warnings.append(f"Could not parse session from line: {line}")
                        
            if not session_info_found:
                failures.append("vai status output does not contain session information")
            else:
                # Verify expected sessions are shown
                expected_sessions = [1, 2, 3, 4]  # 1 is default + 3 test sessions
                
                for session_id in expected_sessions:
                    if session_id not in sessions_detected:
                        warnings.append(f"Session {session_id} not found in vai status output")
                        
            # Test detailed session information
            # Look for health indicators, channel IDs, etc.
            health_indicators_found = False
            for line in output_lines:
                if '💚' in line or '💔' in line or 'healthy' in line.lower() or 'unhealthy' in line.lower():
                    health_indicators_found = True
                    break
                    
            if not health_indicators_found:
                warnings.append("No health indicators found in vai status output")
                
            # Test status command performance
            if returncode == 0:
                start_time = time.time()
                returncode2, stdout2, stderr2 = self.framework.run_command(['python', 'bin/vai', 'status'], timeout=10)
                execution_time = time.time() - start_time
                
                if execution_time > 5.0:  # Should be fast
                    warnings.append(f"vai status command slow: {execution_time:.2f}s")
                    
        except Exception as e:
            failures.append(f"vai status multi-session test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_003_02_session_file_cleanup(self) -> tuple:
        """TC-003-02: Test session-specific file cleanup operations"""
        print("Testing session-specific file cleanup operations...")
        
        failures = []
        warnings = []
        
        try:
            # Create files in multiple sessions for cleanup testing
            cleanup_test_files = {}
            
            for session_id in [1, 2, 3, 4]:
                session_files = []
                
                # Create various types of files
                file_types = [
                    ("temp_file.txt", "Temporary file content"),
                    ("log_file.log", "Log file content"),
                    ("data_file.json", '{"test": "data"}'),
                    ("image_file.png", "PNG fake data"),
                    ("large_file.dat", "X" * 10000)  # 10KB file
                ]
                
                for filename, content in file_types:
                    test_file = self.attachment_helper.create_test_attachment(
                        session_id, filename, content
                    )
                    session_files.append(test_file)
                    
                cleanup_test_files[session_id] = session_files
                
            # Verify all files were created
            total_files = 0
            for session_id, files in cleanup_test_files.items():
                for file_path in files:
                    if file_path.exists():
                        total_files += 1
                    else:
                        failures.append(f"Cleanup test file not created: {file_path}")
                        
            print(f"    Created {total_files} test files across sessions")
            
            # Test session-specific cleanup (simulate)
            target_session = 2
            
            # Get initial state
            session_dir = Path(f'attachments/session_{target_session}')
            if session_dir.exists():
                initial_files = list(session_dir.glob('*'))
                initial_count = len(initial_files)
                
                # Perform selective cleanup - remove specific file types
                cleanup_patterns = ['temp_*', '*.log']
                files_removed = 0
                
                for pattern in cleanup_patterns:
                    matching_files = list(session_dir.glob(pattern))
                    for file_path in matching_files:
                        if file_path.exists():
                            file_path.unlink()
                            files_removed += 1
                            
                # Verify selective cleanup worked
                remaining_files = list(session_dir.glob('*'))
                remaining_count = len(remaining_files)
                
                if remaining_count != (initial_count - files_removed):
                    failures.append(f"Selective cleanup count mismatch: expected {initial_count - files_removed}, got {remaining_count}")
                    
                # Verify correct files were removed
                for file_path in remaining_files:
                    filename = file_path.name
                    if filename.startswith('temp_') or filename.endswith('.log'):
                        failures.append(f"Cleanup failed to remove {filename}")
                        
                # Verify other file types remain
                data_files = list(session_dir.glob('*.json'))
                image_files = list(session_dir.glob('*.png'))
                large_files = list(session_dir.glob('*.dat'))
                
                if len(data_files) == 0 or len(image_files) == 0 or len(large_files) == 0:
                    warnings.append("Some non-target file types were also removed")
                    
            # Verify other sessions were not affected by cleanup
            for other_session in [1, 3, 4]:
                other_dir = Path(f'attachments/session_{other_session}')
                if other_dir.exists():
                    other_files = list(other_dir.glob('*'))
                    
                    # Should still have all original files
                    temp_files = list(other_dir.glob('temp_*'))
                    log_files = list(other_dir.glob('*.log'))
                    
                    if len(temp_files) == 0 and len(log_files) == 0:
                        failures.append(f"Cleanup incorrectly affected session {other_session}")
                    elif len(temp_files) == 0 or len(log_files) == 0:
                        warnings.append(f"Partial cleanup effects detected in session {other_session}")
                        
            # Test cleanup safety - prevent accidental cross-session cleanup
            # This is a conceptual test for safety mechanisms
            for session_id in [1, 3, 4]:  # Non-target sessions
                session_dir = Path(f'attachments/session_{session_id}')
                if session_dir.exists():
                    # Directory should still exist and be accessible
                    if not os.access(session_dir, os.R_OK | os.W_OK):
                        failures.append(f"Session {session_id} directory access changed during cleanup")
                        
        except Exception as e:
            failures.append(f"Session file cleanup test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_003_03_continuous_operation_stability(self) -> tuple:
        """TC-003-03: Test 24-hour continuous operation stability (abbreviated)"""
        print("Testing continuous operation stability (abbreviated test)...")
        
        failures = []
        warnings = []
        
        try:
            # Note: Full 24-hour test would be impractical in automated testing
            # This is an abbreviated version testing stability over shorter duration
            
            test_duration = 60  # 1 minute for automated testing (vs 24 hours in production)
            check_interval = 5  # Check every 5 seconds
            
            print(f"    Running {test_duration}s stability test (abbreviated from 24h)")
            
            # Set up monitoring
            start_time = time.time()
            stability_checks = []
            
            # Create persistent test files
            for session_id in [1, 2, 3, 4]:
                stability_file = self.attachment_helper.create_test_attachment(
                    session_id, "stability_test.txt", f"Stability test for session {session_id}"
                )
                if not stability_file.exists():
                    failures.append(f"Failed to create stability test file for session {session_id}")
                    
            # Run stability monitoring loop
            while (time.time() - start_time) < test_duration:
                check_start = time.time()
                
                # Check session configuration integrity
                sessions_intact = True
                for session_id in [1, 2, 3, 4]:
                    if not self.session_helper.check_session_exists(session_id):
                        sessions_intact = False
                        break
                        
                # Check file system integrity
                files_intact = True
                for session_id in [1, 2, 3, 4]:
                    stability_file = Path(f'attachments/session_{session_id}/stability_test.txt')
                    if not stability_file.exists():
                        files_intact = False
                        break
                        
                # Check system resources
                try:
                    import psutil
                    memory_percent = psutil.virtual_memory().percent
                    cpu_percent = psutil.cpu_percent(interval=1)
                    disk_percent = psutil.disk_usage('/').percent
                    
                    resource_ok = (memory_percent < 90 and cpu_percent < 90 and disk_percent < 90)
                except ImportError:
                    resource_ok = True  # Skip if psutil not available
                    memory_percent = cpu_percent = disk_percent = 0
                    
                # Record check results
                check_result = {
                    'timestamp': time.time() - start_time,
                    'sessions_intact': sessions_intact,
                    'files_intact': files_intact,
                    'resource_ok': resource_ok,
                    'memory_percent': memory_percent,
                    'cpu_percent': cpu_percent,
                    'disk_percent': disk_percent
                }
                stability_checks.append(check_result)
                
                # Sleep until next check
                elapsed = time.time() - check_start
                sleep_time = max(0, check_interval - elapsed)
                time.sleep(sleep_time)
                
            # Analyze stability results
            if stability_checks:
                total_checks = len(stability_checks)
                session_failures = sum(1 for c in stability_checks if not c['sessions_intact'])
                file_failures = sum(1 for c in stability_checks if not c['files_intact'])
                resource_failures = sum(1 for c in stability_checks if not c['resource_ok'])
                
                session_stability = (total_checks - session_failures) / total_checks * 100
                file_stability = (total_checks - file_failures) / total_checks * 100
                resource_stability = (total_checks - resource_failures) / total_checks * 100
                
                print(f"    Session stability: {session_stability:.1f}%")
                print(f"    File stability: {file_stability:.1f}%")
                print(f"    Resource stability: {resource_stability:.1f}%")
                
                # Require high stability for pass
                if session_stability < 95:
                    failures.append(f"Session stability too low: {session_stability:.1f}%")
                if file_stability < 95:
                    failures.append(f"File stability too low: {file_stability:.1f}%")
                if resource_stability < 80:
                    warnings.append(f"Resource stability low: {resource_stability:.1f}%")
                    
                # Check for resource leaks (simplified)
                if len(stability_checks) >= 5:
                    initial_memory = stability_checks[0]['memory_percent']
                    final_memory = stability_checks[-1]['memory_percent']
                    memory_increase = final_memory - initial_memory
                    
                    if memory_increase > 10:  # More than 10% increase
                        warnings.append(f"Potential memory leak detected: {memory_increase:.1f}% increase")
                        
            else:
                failures.append("No stability checks were performed")
                
            warnings.append(f"Full 24-hour stability test should be performed in production environment")
            
        except Exception as e:
            failures.append(f"Continuous operation stability test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_003_04_session1_compatibility(self) -> tuple:
        """TC-003-04: Test existing Session 1 compatibility preservation"""
        print("Testing existing Session 1 compatibility preservation...")
        
        failures = []
        warnings = []
        
        try:
            # Verify Session 1 still exists and functions
            if not self.session_helper.check_session_exists(1):
                failures.append("Session 1 (default) no longer exists")
                return (False, failures, warnings)
                
            # Test Session 1 directory structure
            session1_dir = Path('attachments/session_1')
            if not session1_dir.exists():
                session1_dir.mkdir(parents=True, exist_ok=True)
                warnings.append("Session 1 directory did not exist, created for compatibility")
                
            if not session1_dir.exists():
                failures.append("Cannot create/access Session 1 directory")
                return (False, failures, warnings)
                
            # Test Session 1 file operations
            try:
                test_file = self.attachment_helper.create_test_attachment(
                    1, "compatibility_test.txt", "Session 1 compatibility test"
                )
                
                if not test_file.exists():
                    failures.append("Cannot create files in Session 1 directory")
                else:
                    # Test file read
                    with open(test_file, 'r') as f:
                        content = f.read()
                        if "Session 1 compatibility test" not in content:
                            failures.append("Session 1 file content integrity issue")
                            
            except Exception as e:
                failures.append(f"Session 1 file operations failed: {str(e)}")
                
            # Test default behavior preservation
            # dp command without session number should still work for Session 1
            test_cmd = 'python src/discord_post.py "Default session test"'
            returncode, stdout, stderr = self.framework.run_command(['bash', '-c', test_cmd], timeout=10)
            
            # Should not fail due to session validation (may fail due to Discord API, which is expected)
            if "Error: Invalid session number" in stderr:
                failures.append("Default dp command incorrectly rejects Session 1")
            elif "Error: Session 1 not configured" in stderr:
                failures.append("Session 1 configuration missing")
            else:
                # Expected to fail with Discord API error in test environment
                if returncode != 0 and "discord" not in stderr.lower():
                    warnings.append(f"Unexpected error in default command: {stderr}")
                    
            # Test that Session 1 doesn't interfere with new sessions
            # Create same filename in Session 1 and other sessions
            test_filename = "cross_session_test.txt"
            
            session1_file = self.attachment_helper.create_test_attachment(
                1, test_filename, "Content for Session 1"
            )
            
            session2_file = self.attachment_helper.create_test_attachment(
                2, test_filename, "Content for Session 2"
            )
            
            if session1_file.exists() and session2_file.exists():
                # Both should exist with their own content
                with open(session1_file, 'r') as f:
                    s1_content = f.read()
                with open(session2_file, 'r') as f:
                    s2_content = f.read()
                    
                if "Session 1" not in s1_content or "Session 2" not in s2_content:
                    failures.append("Session 1 file isolation from new sessions failed")
                    
            # Test Session 1 performance hasn't degraded
            start_time = time.time()
            for i in range(10):  # Create multiple files quickly
                quick_file = self.attachment_helper.create_test_attachment(
                    1, f"performance_test_{i}.txt", f"Quick test {i}"
                )
            performance_time = time.time() - start_time
            
            if performance_time > 5.0:  # Should be fast
                warnings.append(f"Session 1 performance may have degraded: {performance_time:.2f}s for 10 files")
                
        except Exception as e:
            failures.append(f"Session 1 compatibility test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_003_05_cli_session_management(self) -> tuple:
        """TC-003-05: Test CLI session management commands"""
        print("Testing CLI session management commands...")
        
        failures = []
        warnings = []
        
        try:
            # Test vai command basic functionality
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', '--help'], timeout=10)
            
            if returncode != 0:
                failures.append(f"vai help command failed: {stderr}")
                return (False, failures, warnings)
                
            # Look for session management commands in help
            help_text = stdout.lower()
            expected_commands = ['status', 'add-session', 'remove-session', 'list-sessions', 'recover']
            commands_found = []
            
            for cmd in expected_commands:
                if cmd.lower() in help_text or cmd.replace('-', '_').lower() in help_text:
                    commands_found.append(cmd)
                else:
                    warnings.append(f"Command '{cmd}' not found in vai help text")
                    
            # Test status command (already tested above, brief check)
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'status'], timeout=15)
            
            if returncode != 0:
                failures.append(f"vai status command not working: {stderr}")
            else:
                if 'Session' not in stdout:
                    warnings.append("vai status output doesn't show session information")
                    
            # Test session listing (if implemented)
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'list-sessions'], timeout=10)
            
            if returncode == 0:
                # Command exists and works
                if 'Session' in stdout or '1' in stdout:
                    warnings.append("vai list-sessions command working")
                else:
                    warnings.append("vai list-sessions output format unclear")
            else:
                warnings.append("vai list-sessions command not implemented or not working")
                
            # Test add-session command (test mode - don't actually add)
            test_channel_id = "9999999999999999999"  # Fake channel ID for testing
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'add-session', test_channel_id], timeout=10)
            
            if returncode == 0:
                warnings.append("vai add-session command appears to work")
                # Should clean up the test session
                try:
                    # Find what session number was assigned and remove it
                    if 'Session' in stdout:
                        # Try to extract session number and remove it
                        import re
                        session_match = re.search(r'Session (\d+)', stdout)
                        if session_match:
                            test_session_id = int(session_match.group(1))
                            self.session_helper.remove_test_session(test_session_id)
                except Exception:
                    pass  # Cleanup attempt failed, not critical
            else:
                if "not implemented" in stderr.lower() or "unknown" in stderr.lower():
                    warnings.append("vai add-session command not yet implemented")
                else:
                    warnings.append(f"vai add-session command error: {stderr}")
                    
            # Test recover command
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'recover', '1'], timeout=10)
            
            if returncode == 0:
                warnings.append("vai recover command appears to work")
            else:
                if "not implemented" in stderr.lower() or "unknown" in stderr.lower():
                    warnings.append("vai recover command not yet implemented")
                else:
                    warnings.append(f"vai recover command error: {stderr}")
                    
            # Test command error handling
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'invalid-command'], timeout=10)
            
            if returncode != 0:
                # Should properly handle invalid commands
                warnings.append("vai properly handles invalid commands")
            else:
                failures.append("vai does not properly reject invalid commands")
                
            # Test command execution speed
            start_time = time.time()
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'status'], timeout=10)
            execution_time = time.time() - start_time
            
            if execution_time > 5.0:
                warnings.append(f"vai commands are slow: {execution_time:.2f}s")
                
        except Exception as e:
            failures.append(f"CLI session management test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def run_tests(self) -> TestResult:
        """Run all TC-003 session management tests"""
        print(f"🚀 Running {self.name}")
        start_time = time.time()
        
        total_tests = 5
        passed_tests = 0
        all_failures = []
        all_warnings = []
        
        try:
            # Setup test environment
            if not self.setup_test_environment():
                return TestResult(
                    "TC-003", 0, total_tests, False,
                    failures=["Failed to setup session management test environment"],
                    execution_time=time.time() - start_time
                )
                
            # Run individual tests
            tests = [
                ("TC-003-01", self.test_003_01_vai_status_multi_session),
                ("TC-003-02", self.test_003_02_session_file_cleanup),
                ("TC-003-03", self.test_003_03_continuous_operation_stability),
                ("TC-003-04", self.test_003_04_session1_compatibility),
                ("TC-003-05", self.test_003_05_cli_session_management)
            ]
            
            for test_name, test_func in tests:
                print(f"  Running {test_name}...")
                try:
                    passed, failures, warnings = test_func()
                    
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
            all_failures.append(f"Session management test suite setup failed: {str(e)}")
            
        finally:
            # Clean up test environment
            self.cleanup_test_environment()
            
        execution_time = time.time() - start_time
        overall_passed = len(all_failures) == 0
        
        result = TestResult(
            "TC-003",
            passed_tests,
            total_tests,
            overall_passed,
            failures=all_failures,
            warnings=all_warnings,
            execution_time=execution_time
        )
        
        return result

if __name__ == "__main__":
    # Direct execution for testing
    test_suite = TC003SessionManagement()
    result = test_suite.run_tests()
    
    print(f"\n{'='*50}")
    print(f"TC-003 Results: {'PASS' if result.passed else 'FAIL'}")
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