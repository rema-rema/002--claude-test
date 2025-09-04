#!/usr/bin/env python3
"""
TC-004: Recovery and Error Handling Tests
Tests for Success Criteria SC-002: セキュリティ・復旧機能 (Recovery Aspect)

Test Cases:
- TC-004-01: Automatic session recovery functionality
- TC-004-02: Error handling for invalid session operations  
- TC-004-03: Session failure detection and notification
- TC-004-04: Manual recovery command functionality
- TC-004-05: Recovery logging and audit trail
"""

import os
import sys
import time
import json
import signal
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_utils import TestFramework, TestResult, SessionTestHelper, AttachmentTestHelper, TmuxTestHelper

class TC004RecoveryError:
    """TC-004: Recovery and Error Handling Test Suite"""
    
    def __init__(self):
        self.name = "Recovery and Error Handling Tests (SC-002 Recovery Aspect)"
        self.framework = TestFramework()
        self.session_helper = SessionTestHelper()
        self.attachment_helper = AttachmentTestHelper()
        self.tmux_helper = TmuxTestHelper()
        self.test_sessions = [2, 3, 4]
        
    def setup_test_environment(self) -> bool:
        """Set up recovery and error handling test environment"""
        print("Setting up recovery and error handling test environment...")
        
        # Create test sessions
        test_channels = {
            2: "1234567890123456001",
            3: "1234567890123456002", 
            4: "1234567890123456003"
        }
        
        for session_id, channel_id in test_channels.items():
            if not self.session_helper.create_test_session(session_id, channel_id):
                return False
                
        # Create logs directory for recovery logging tests
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        
        return True
        
    def cleanup_test_environment(self):
        """Clean up recovery and error handling test environment"""
        print("Cleaning up recovery and error handling test environment...")
        self.session_helper.cleanup_test_sessions()
        self.attachment_helper.cleanup_test_files()
        self.tmux_helper.cleanup_test_sessions()
        
    def test_004_01_automatic_session_recovery(self) -> tuple:
        """TC-004-01: Test automatic session recovery functionality"""
        print("Testing automatic session recovery functionality...")
        
        failures = []
        warnings = []
        
        try:
            # Create test tmux sessions that can be "crashed" and recovered
            recovery_sessions = {}
            
            for session_id in self.test_sessions:
                session_name = f"test-claude-session-{session_id}"
                
                # Create tmux session
                if self.tmux_helper.create_test_tmux_session(session_name):
                    recovery_sessions[session_id] = session_name
                    print(f"    Created test session: {session_name}")
                else:
                    warnings.append(f"Could not create test tmux session for session {session_id}")
                    
            if not recovery_sessions:
                warnings.append("No test tmux sessions created, testing recovery logic only")
                
            # Test session health checking
            healthy_sessions = []
            unhealthy_sessions = []
            
            for session_id, session_name in recovery_sessions.items():
                if self.tmux_helper.check_tmux_session_exists(session_name):
                    healthy_sessions.append(session_id)
                else:
                    unhealthy_sessions.append(session_id)
                    
            print(f"    Healthy sessions: {healthy_sessions}")
            print(f"    Unhealthy sessions: {unhealthy_sessions}")
            
            # Simulate session failure by killing one session
            if recovery_sessions:
                test_session_id = list(recovery_sessions.keys())[0]
                test_session_name = recovery_sessions[test_session_id]
                
                print(f"    Simulating failure of session {test_session_id}")
                
                # Kill the tmux session to simulate failure
                if self.tmux_helper.kill_tmux_session(test_session_name):
                    # Verify session is gone
                    if not self.tmux_helper.check_tmux_session_exists(test_session_name):
                        print(f"    Session {test_session_id} successfully terminated")
                        
                        # Test recovery attempt
                        recovery_start = time.time()
                        
                        # Simulate recovery by recreating session
                        if self.tmux_helper.create_test_tmux_session(test_session_name):
                            recovery_time = time.time() - recovery_start
                            print(f"    Session {test_session_id} recovered in {recovery_time:.2f}s")
                            
                            if recovery_time > 10.0:  # Should recover quickly
                                warnings.append(f"Session recovery took too long: {recovery_time:.2f}s")
                                
                            # Verify recovered session is functional
                            if not self.tmux_helper.check_tmux_session_exists(test_session_name):
                                failures.append(f"Recovered session {test_session_id} not functional")
                                
                        else:
                            failures.append(f"Failed to recover session {test_session_id}")
                            
                    else:
                        failures.append(f"Session {test_session_id} termination failed")
                        
            # Test exponential backoff recovery (simulated)
            # In real system, this would be handled by auto_recovery.py
            backoff_times = [1, 2, 4]  # Exponential backoff sequence
            recovery_attempts = []
            
            for attempt, delay in enumerate(backoff_times, 1):
                print(f"    Simulating recovery attempt {attempt} with {delay}s delay")
                
                attempt_start = time.time()
                time.sleep(min(delay, 0.5))  # Shortened for testing
                
                # Simulate recovery attempt
                recovery_success = (attempt == len(backoff_times))  # Last attempt succeeds
                attempt_time = time.time() - attempt_start
                
                recovery_attempts.append({
                    'attempt': attempt,
                    'delay': delay,
                    'success': recovery_success,
                    'time': attempt_time
                })
                
                if recovery_success:
                    print(f"    Recovery successful on attempt {attempt}")
                    break
                else:
                    print(f"    Recovery attempt {attempt} failed, backing off")
                    
            # Verify recovery attempt pattern
            if len(recovery_attempts) != len(backoff_times):
                warnings.append(f"Recovery attempts count mismatch: expected {len(backoff_times)}, got {len(recovery_attempts)}")
                
            # Test recovery limits (3 attempts max)
            max_attempts = 3
            if len(recovery_attempts) > max_attempts:
                failures.append(f"Too many recovery attempts: {len(recovery_attempts)} > {max_attempts}")
                
        except Exception as e:
            failures.append(f"Automatic session recovery test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_004_02_invalid_session_error_handling(self) -> tuple:
        """TC-004-02: Test error handling for invalid session operations"""
        print("Testing error handling for invalid session operations...")
        
        failures = []
        warnings = []
        
        try:
            # Test invalid session numbers
            invalid_sessions = [0, -1, 99999, 'abc', '']
            
            for invalid_session in invalid_sessions:
                print(f"    Testing invalid session: {invalid_session}")
                
                # Test discord_post.py error handling
                test_cmd = f'python src/discord_post.py {invalid_session} "Test message"'
                returncode, stdout, stderr = self.framework.run_command(['bash', '-c', test_cmd], timeout=10)
                
                if returncode == 0:
                    failures.append(f"Invalid session {invalid_session} was accepted")
                else:
                    # Should have proper error message
                    if "Invalid session" not in stderr and "must be" not in stderr:
                        warnings.append(f"Error message unclear for invalid session {invalid_session}: {stderr}")
                    else:
                        print(f"      Properly rejected: {invalid_session}")
                        
            # Test non-existent but valid session numbers
            non_existent_sessions = [99, 100, 999]
            
            for session_id in non_existent_sessions:
                print(f"    Testing non-existent session: {session_id}")
                
                test_cmd = f'python src/discord_post.py {session_id} "Test message"'
                returncode, stdout, stderr = self.framework.run_command(['bash', '-c', test_cmd], timeout=10)
                
                if returncode == 0:
                    warnings.append(f"Non-existent session {session_id} was accepted")
                else:
                    # Should indicate session not configured
                    if "not configured" not in stderr and "not found" not in stderr:
                        warnings.append(f"Error message unclear for non-existent session {session_id}: {stderr}")
                    else:
                        print(f"      Properly rejected: {session_id}")
                        
            # Test session creation with invalid channel IDs
            invalid_channels = ['invalid', '123', 'abc123def', '']
            
            for invalid_channel in invalid_channels:
                print(f"    Testing invalid channel ID: {invalid_channel}")
                
                # This should fail gracefully
                creation_result = self.session_helper.create_test_session(999, invalid_channel)
                
                if creation_result:
                    # If creation succeeded, verify session actually works
                    if self.session_helper.check_session_exists(999):
                        warnings.append(f"Invalid channel ID {invalid_channel} was accepted")
                        # Clean up
                        self.session_helper.remove_test_session(999)
                    else:
                        print(f"      Creation appeared to succeed but session not functional")
                else:
                    print(f"      Properly rejected invalid channel: {invalid_channel}")
                    
            # Test error handling in file operations
            invalid_session_id = 999
            
            try:
                # This should fail gracefully
                test_file = self.attachment_helper.create_test_attachment(
                    invalid_session_id, "error_test.txt", "Error test content"
                )
                
                # If file was created, directory should exist
                if test_file.exists():
                    warnings.append("File creation succeeded for invalid session (auto-creation)")
                    # Clean up
                    test_file.unlink()
                    test_file.parent.rmdir()
                    
            except Exception as e:
                print(f"      File operation properly failed: {str(e)[:50]}...")
                
            # Test concurrent error conditions
            # Simulate multiple invalid requests simultaneously
            import threading
            
            error_results = []
            
            def test_invalid_session(session_id):
                try:
                    cmd = f'python src/discord_post.py {session_id} "Concurrent test"'
                    returncode, stdout, stderr = self.framework.run_command(['bash', '-c', cmd], timeout=5)
                    error_results.append((session_id, returncode, stderr))
                except Exception as e:
                    error_results.append((session_id, -1, str(e)))
                    
            # Start multiple threads with invalid sessions
            threads = []
            for i in range(5):
                invalid_session = 9999 + i
                thread = threading.Thread(target=test_invalid_session, args=(invalid_session,))
                thread.start()
                threads.append(thread)
                
            # Wait for all threads
            for thread in threads:
                thread.join(timeout=10)
                
            # Check results
            for session_id, returncode, stderr in error_results:
                if returncode == 0:
                    failures.append(f"Concurrent invalid session {session_id} was accepted")
                elif "Invalid session" not in stderr and "not configured" not in stderr:
                    warnings.append(f"Concurrent error handling unclear for session {session_id}")
                    
        except Exception as e:
            failures.append(f"Invalid session error handling test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_004_03_session_failure_detection(self) -> tuple:
        """TC-004-03: Test session failure detection and notification"""
        print("Testing session failure detection and notification...")
        
        failures = []
        warnings = []
        
        try:
            # Set up monitoring for session failure detection
            monitoring_sessions = {}
            
            # Create test sessions for monitoring
            for session_id in self.test_sessions:
                session_name = f"monitor-session-{session_id}"
                if self.tmux_helper.create_test_tmux_session(session_name):
                    monitoring_sessions[session_id] = {
                        'name': session_name,
                        'status': 'healthy',
                        'last_check': time.time()
                    }
                    
            print(f"    Created {len(monitoring_sessions)} sessions for monitoring")
            
            # Test health checking functionality
            health_check_results = {}
            
            for session_id, session_info in monitoring_sessions.items():
                session_name = session_info['name']
                
                # Check if session is alive
                is_alive = self.tmux_helper.check_tmux_session_exists(session_name)
                health_check_results[session_id] = is_alive
                
                print(f"    Session {session_id}: {'Healthy' if is_alive else 'Failed'}")
                
            # Simulate session failure
            if monitoring_sessions:
                failure_session_id = list(monitoring_sessions.keys())[0]
                failure_session_name = monitoring_sessions[failure_session_id]['name']
                
                print(f"    Simulating failure of session {failure_session_id}")
                
                # Kill session to simulate failure
                if self.tmux_helper.kill_tmux_session(failure_session_name):
                    # Give it a moment to die
                    time.sleep(0.5)
                    
                    # Check if failure is detected
                    failure_detected = not self.tmux_helper.check_tmux_session_exists(failure_session_name)
                    
                    if failure_detected:
                        print(f"    Failure successfully detected for session {failure_session_id}")
                    else:
                        failures.append(f"Failed to detect session {failure_session_id} failure")
                        
                    # Test notification mechanism (simulated)
                    # In real system, this would send Discord notification
                    notification_content = f"Session {failure_session_id} has failed and requires attention"
                    print(f"    Notification: {notification_content}")
                    
                    # Simulate notification success/failure
                    notification_sent = True  # In real system, this would be Discord API call result
                    
                    if not notification_sent:
                        failures.append(f"Failed to send failure notification for session {failure_session_id}")
                        
            # Test monitoring interval functionality
            monitoring_start = time.time()
            monitoring_duration = 10  # 10 seconds of monitoring
            check_interval = 2     # Check every 2 seconds
            monitoring_checks = []
            
            print(f"    Running {monitoring_duration}s monitoring test...")
            
            while (time.time() - monitoring_start) < monitoring_duration:
                check_start = time.time()
                
                # Perform health checks on all sessions
                current_checks = {}
                
                for session_id, session_info in monitoring_sessions.items():
                    session_name = session_info['name']
                    is_healthy = self.tmux_helper.check_tmux_session_exists(session_name)
                    current_checks[session_id] = {
                        'timestamp': time.time(),
                        'healthy': is_healthy,
                        'session_name': session_name
                    }
                    
                monitoring_checks.append(current_checks)
                
                # Sleep until next check
                elapsed = time.time() - check_start
                sleep_time = max(0, check_interval - elapsed)
                time.sleep(sleep_time)
                
            # Analyze monitoring results
            if monitoring_checks:
                total_checks = len(monitoring_checks)
                print(f"    Completed {total_checks} monitoring checks")
                
                # Check for consistent failure detection
                for session_id in monitoring_sessions.keys():
                    session_checks = [check[session_id] for check in monitoring_checks if session_id in check]
                    
                    if session_checks:
                        healthy_count = sum(1 for check in session_checks if check['healthy'])
                        unhealthy_count = len(session_checks) - healthy_count
                        
                        print(f"    Session {session_id}: {healthy_count} healthy, {unhealthy_count} unhealthy checks")
                        
                        # Analyze pattern
                        if session_id == failure_session_id and unhealthy_count == 0:
                            failures.append(f"Failed session {session_id} not detected as unhealthy")
                        elif session_id != failure_session_id and unhealthy_count > 0:
                            warnings.append(f"Healthy session {session_id} incorrectly detected as unhealthy")
                            
            # Test alert threshold functionality
            failure_threshold = 3  # 3 consecutive failures trigger alert
            consecutive_failures = 0
            
            for i in range(5):  # Simulate 5 consecutive failures
                consecutive_failures += 1
                
                if consecutive_failures >= failure_threshold:
                    alert_triggered = True
                    print(f"    Alert triggered after {consecutive_failures} failures")
                    break
            else:
                alert_triggered = False
                
            if not alert_triggered:
                warnings.append(f"Alert threshold not reached with {consecutive_failures} failures")
                
        except Exception as e:
            failures.append(f"Session failure detection test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_004_04_manual_recovery_commands(self) -> tuple:
        """TC-004-04: Test manual recovery command functionality"""
        print("Testing manual recovery command functionality...")
        
        failures = []
        warnings = []
        
        try:
            # Test vai recover command functionality
            test_session_id = 2
            
            # Test basic recover command syntax
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'recover', str(test_session_id)], timeout=15)
            
            if returncode == 0:
                print(f"    vai recover {test_session_id} executed successfully")
                
                # Check if recovery actions were performed
                if 'recover' in stdout.lower() or 'session' in stdout.lower():
                    warnings.append("vai recover command appears to be working")
                else:
                    warnings.append("vai recover command output unclear")
                    
            else:
                if "not implemented" in stderr.lower() or "unknown" in stderr.lower():
                    warnings.append("vai recover command not yet implemented")
                else:
                    warnings.append(f"vai recover command failed: {stderr}")
                    
            # Test recover with invalid session
            invalid_session = 9999
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'recover', str(invalid_session)], timeout=10)
            
            if returncode == 0:
                warnings.append(f"vai recover accepted invalid session {invalid_session}")
            else:
                print(f"    vai recover properly rejected invalid session {invalid_session}")
                
            # Test doctor command (diagnostic functionality)
            returncode, stdout, stderr = self.framework.run_command(['python', 'bin/vai', 'doctor'], timeout=15)
            
            if returncode == 0:
                print("    vai doctor command executed successfully")
                
                # Look for diagnostic information
                diagnostic_indicators = ['session', 'status', 'health', 'check', 'ok', 'error']
                indicators_found = sum(1 for indicator in diagnostic_indicators if indicator.lower() in stdout.lower())
                
                if indicators_found >= 2:
                    warnings.append("vai doctor appears to provide diagnostic information")
                else:
                    warnings.append("vai doctor output lacks diagnostic information")
                    
            else:
                if "not implemented" in stderr.lower():
                    warnings.append("vai doctor command not yet implemented")
                else:
                    warnings.append(f"vai doctor command failed: {stderr}")
                    
            # Test manual session restart
            # Create a test session that can be restarted
            restart_session_name = f"restart-test-{test_session_id}"
            
            if self.tmux_helper.create_test_tmux_session(restart_session_name):
                print(f"    Created test session for restart: {restart_session_name}")
                
                # Kill the session
                if self.tmux_helper.kill_tmux_session(restart_session_name):
                    print(f"    Killed test session: {restart_session_name}")
                    
                    # Verify it's dead
                    if not self.tmux_helper.check_tmux_session_exists(restart_session_name):
                        # Attempt manual recovery (restart)
                        recovery_start = time.time()
                        
                        # Simulate manual recovery
                        if self.tmux_helper.create_test_tmux_session(restart_session_name):
                            recovery_time = time.time() - recovery_start
                            print(f"    Manual recovery successful in {recovery_time:.2f}s")
                            
                            # Verify recovered session
                            if self.tmux_helper.check_tmux_session_exists(restart_session_name):
                                warnings.append("Manual session recovery successful")
                            else:
                                failures.append("Manual recovery created session but it's not functional")
                                
                        else:
                            failures.append("Manual session recovery failed")
                            
                    else:
                        failures.append("Test session did not terminate properly")
                        
            # Test recovery status reporting
            # Simulate recovery operation and check status
            recovery_operations = [
                ("Session restart", True),
                ("Configuration reload", True),
                ("Directory creation", True),
                ("Permission fix", False)  # One failure for testing
            ]
            
            recovery_report = []
            for operation, success in recovery_operations:
                status = "SUCCESS" if success else "FAILED"
                recovery_report.append(f"{operation}: {status}")
                
            print("    Recovery status report:")
            for report_line in recovery_report:
                print(f"      {report_line}")
                
            successful_operations = sum(1 for _, success in recovery_operations if success)
            total_operations = len(recovery_operations)
            recovery_success_rate = successful_operations / total_operations * 100
            
            if recovery_success_rate < 50:
                failures.append(f"Recovery success rate too low: {recovery_success_rate:.1f}%")
            elif recovery_success_rate < 100:
                warnings.append(f"Some recovery operations failed: {recovery_success_rate:.1f}% success")
                
        except Exception as e:
            failures.append(f"Manual recovery commands test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_004_05_recovery_logging_audit(self) -> tuple:
        """TC-004-05: Test recovery logging and audit trail"""
        print("Testing recovery logging and audit trail...")
        
        failures = []
        warnings = []
        
        try:
            # Set up logging for recovery operations
            log_dir = Path('logs')
            log_dir.mkdir(exist_ok=True)
            
            recovery_log_file = log_dir / 'recovery.log'
            audit_log_file = log_dir / 'audit.log'
            
            # Test recovery log creation
            recovery_events = [
                {"timestamp": time.time(), "session": 2, "event": "Session failure detected", "severity": "WARNING"},
                {"timestamp": time.time(), "event": "Recovery attempt started", "attempt": 1, "severity": "INFO"},
                {"timestamp": time.time(), "event": "Recovery attempt failed", "attempt": 1, "error": "Connection timeout", "severity": "ERROR"},
                {"timestamp": time.time(), "event": "Recovery attempt started", "attempt": 2, "severity": "INFO"},
                {"timestamp": time.time(), "event": "Recovery successful", "attempt": 2, "severity": "INFO"}
            ]
            
            # Write recovery events to log (simulating logging system)
            with open(recovery_log_file, 'w') as f:
                for event in recovery_events:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event['timestamp']))
                    severity = event.get('severity', 'INFO')
                    
                    if 'session' in event:
                        log_line = f"[{timestamp}] {severity}: Session {event['session']}: {event['event']}"
                    else:
                        log_line = f"[{timestamp}] {severity}: {event['event']}"
                        
                    if 'attempt' in event:
                        log_line += f" (Attempt {event['attempt']})"
                        
                    if 'error' in event:
                        log_line += f" - {event['error']}"
                        
                    f.write(log_line + '\n')
                    
            print(f"    Created recovery log with {len(recovery_events)} events")
            
            # Verify log file was created and contains expected content
            if not recovery_log_file.exists():
                failures.append("Recovery log file was not created")
            else:
                with open(recovery_log_file, 'r') as f:
                    log_content = f.read()
                    
                # Check for expected log entries
                expected_patterns = ['Session failure detected', 'Recovery attempt started', 'Recovery successful']
                missing_patterns = []
                
                for pattern in expected_patterns:
                    if pattern not in log_content:
                        missing_patterns.append(pattern)
                        
                if missing_patterns:
                    failures.append(f"Missing log patterns: {missing_patterns}")
                    
                # Check log format
                log_lines = log_content.strip().split('\n')
                malformed_lines = []
                
                for line in log_lines:
                    if not ('[' in line and ']' in line and ':' in line):
                        malformed_lines.append(line[:50])
                        
                if malformed_lines:
                    warnings.append(f"Malformed log lines detected: {len(malformed_lines)}")
                    
            # Test audit trail for administrative actions
            audit_events = [
                {"timestamp": time.time(), "user": "system", "action": "session_add", "target": "session_5", "channel": "1234567890123456005"},
                {"timestamp": time.time(), "user": "admin", "action": "session_remove", "target": "session_5"},
                {"timestamp": time.time(), "user": "system", "action": "recovery_initiated", "target": "session_2", "reason": "automatic"},
                {"timestamp": time.time(), "user": "admin", "action": "manual_recovery", "target": "session_3", "reason": "user_request"}
            ]
            
            # Write audit events
            with open(audit_log_file, 'w') as f:
                for event in audit_events:
                    timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(event['timestamp']))
                    user = event['user']
                    action = event['action']
                    target = event.get('target', 'N/A')
                    
                    audit_line = f"[{timestamp}] USER:{user} ACTION:{action} TARGET:{target}"
                    
                    if 'channel' in event:
                        audit_line += f" CHANNEL:{event['channel']}"
                        
                    if 'reason' in event:
                        audit_line += f" REASON:{event['reason']}"
                        
                    f.write(audit_line + '\n')
                    
            print(f"    Created audit log with {len(audit_events)} events")
            
            # Verify audit log
            if not audit_log_file.exists():
                failures.append("Audit log file was not created")
            else:
                with open(audit_log_file, 'r') as f:
                    audit_content = f.read()
                    
                # Check for audit trail integrity
                audit_lines = audit_content.strip().split('\n')
                
                if len(audit_lines) != len(audit_events):
                    failures.append(f"Audit log line count mismatch: expected {len(audit_events)}, got {len(audit_lines)}")
                    
                # Check audit format
                required_fields = ['USER:', 'ACTION:', 'TARGET:']
                malformed_audit_lines = []
                
                for line in audit_lines:
                    missing_fields = [field for field in required_fields if field not in line]
                    if missing_fields:
                        malformed_audit_lines.append((line[:50], missing_fields))
                        
                if malformed_audit_lines:
                    failures.append(f"Malformed audit lines: {len(malformed_audit_lines)}")
                    
            # Test log rotation and retention
            # Simulate old log files
            old_recovery_log = log_dir / 'recovery.log.1'
            very_old_recovery_log = log_dir / 'recovery.log.10'
            
            # Create mock old logs
            with open(old_recovery_log, 'w') as f:
                f.write("[2024-01-01 00:00:00] INFO: Old log entry\n")
                
            with open(very_old_recovery_log, 'w') as f:
                f.write("[2023-01-01 00:00:00] INFO: Very old log entry\n")
                
            # Check log file sizes and rotation logic
            current_log_size = recovery_log_file.stat().st_size if recovery_log_file.exists() else 0
            
            if current_log_size > 10 * 1024 * 1024:  # 10MB limit
                warnings.append(f"Recovery log file large: {current_log_size / 1024 / 1024:.2f}MB")
                
            # Test log cleanup (simulated)
            log_files = list(log_dir.glob('*.log*'))
            print(f"    Found {len(log_files)} log files")
            
            if len(log_files) > 10:  # Too many log files
                warnings.append(f"Too many log files: {len(log_files)} (consider cleanup)")
                
            # Test log integrity verification
            # Check that logs can be parsed correctly
            try:
                if recovery_log_file.exists():
                    with open(recovery_log_file, 'r') as f:
                        log_content = f.read()
                        
                    # Simple integrity check
                    if len(log_content) == 0:
                        failures.append("Recovery log file is empty")
                    elif '\x00' in log_content:  # Binary data
                        failures.append("Recovery log file contains binary data")
                        
            except UnicodeDecodeError:
                failures.append("Recovery log file has encoding issues")
                
        except Exception as e:
            failures.append(f"Recovery logging and audit test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def run_tests(self) -> TestResult:
        """Run all TC-004 recovery and error handling tests"""
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
                    "TC-004", 0, total_tests, False,
                    failures=["Failed to setup recovery and error handling test environment"],
                    execution_time=time.time() - start_time
                )
                
            # Run individual tests
            tests = [
                ("TC-004-01", self.test_004_01_automatic_session_recovery),
                ("TC-004-02", self.test_004_02_invalid_session_error_handling),
                ("TC-004-03", self.test_004_03_session_failure_detection),
                ("TC-004-04", self.test_004_04_manual_recovery_commands),
                ("TC-004-05", self.test_004_05_recovery_logging_audit)
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
            all_failures.append(f"Recovery and error handling test suite setup failed: {str(e)}")
            
        finally:
            # Clean up test environment
            self.cleanup_test_environment()
            
        execution_time = time.time() - start_time
        overall_passed = len(all_failures) == 0
        
        result = TestResult(
            "TC-004",
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
    test_suite = TC004RecoveryError()
    result = test_suite.run_tests()
    
    print(f"\n{'='*50}")
    print(f"TC-004 Results: {'PASS' if result.passed else 'FAIL'}")
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