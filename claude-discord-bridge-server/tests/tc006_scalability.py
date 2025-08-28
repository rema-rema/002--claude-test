#!/usr/bin/env python3
"""
TC-006: Scalability Tests
Tests for Success Criteria SC-006: 拡張性検証

Test Cases:
- TC-006-01: Dynamic session addition (Session 5)
- TC-006-02: Automatic session_N directory creation
- TC-006-03: sessions.json dynamic entry addition
- TC-006-04: Multi-session scaling (up to 10 sessions)
- TC-006-05: Parallel session operations validation
"""

import os
import sys
import time
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_utils import TestFramework, TestResult, SessionTestHelper, AttachmentTestHelper, TmuxTestHelper

class TC006Scalability:
    """TC-006: Scalability Test Suite"""
    
    def __init__(self):
        self.name = "Scalability Tests (SC-006)"
        self.framework = TestFramework()
        self.session_helper = SessionTestHelper()
        self.attachment_helper = AttachmentTestHelper()
        self.tmux_helper = TmuxTestHelper()
        self.scalability_test_sessions = list(range(5, 15))  # Sessions 5-14 for scalability testing
        
    def setup_test_environment(self) -> bool:
        """Set up scalability test environment"""
        print("Setting up scalability test environment...")
        
        # Start with basic test sessions
        initial_sessions = {
            2: "1234567890123456001",
            3: "1234567890123456002", 
            4: "1234567890123456003"
        }
        
        for session_id, channel_id in initial_sessions.items():
            if not self.session_helper.create_test_session(session_id, channel_id):
                return False
                
        return True
        
    def cleanup_test_environment(self):
        """Clean up scalability test environment"""
        print("Cleaning up scalability test environment...")
        
        # Clean up all test sessions including scalability sessions
        for session_id in self.scalability_test_sessions:
            self.session_helper.remove_test_session(session_id)
            
        self.session_helper.cleanup_test_sessions()
        self.attachment_helper.cleanup_test_files()
        self.tmux_helper.cleanup_test_sessions()
        
    def test_006_01_dynamic_session_addition(self) -> tuple:
        """TC-006-01: Test dynamic session addition (Session 5)"""
        print("Testing dynamic session addition (Session 5)...")
        
        failures = []
        warnings = []
        
        try:
            # Test adding Session 5 dynamically
            new_session_id = 5
            new_channel_id = "1234567890123456005"
            
            print(f"    Adding Session {new_session_id} dynamically...")
            
            # Check initial state - Session 5 should not exist
            if self.session_helper.check_session_exists(new_session_id):
                warnings.append(f"Session {new_session_id} already exists before dynamic addition test")
                # Remove it for clean test
                self.session_helper.remove_test_session(new_session_id)
                
            # Perform dynamic addition
            addition_start = time.time()
            
            success = self.session_helper.create_test_session(new_session_id, new_channel_id)
            
            addition_time = time.time() - addition_start
            
            if not success:
                failures.append(f"Failed to dynamically add Session {new_session_id}")
                return (False, failures, warnings)
                
            print(f"    Session {new_session_id} added in {addition_time:.2f}s")
            
            if addition_time > 5.0:  # Should be fast
                warnings.append(f"Dynamic session addition slow: {addition_time:.2f}s")
                
            # Verify session was actually added
            if not self.session_helper.check_session_exists(new_session_id):
                failures.append(f"Session {new_session_id} not found after dynamic addition")
                return (False, failures, warnings)
                
            # Verify channel mapping is correct
            retrieved_channel = self.session_helper.get_session_channel(new_session_id)
            if retrieved_channel != new_channel_id:
                failures.append(f"Session {new_session_id} channel mapping incorrect: expected {new_channel_id}, got {retrieved_channel}")
                
            # Test immediate functionality of new session
            # Create attachment directory
            session_dir = Path(f'attachments/session_{new_session_id}')
            session_dir.mkdir(parents=True, exist_ok=True)
            
            if not session_dir.exists():
                failures.append(f"Could not create directory for new Session {new_session_id}")
            else:
                # Test file operations in new session
                test_file = self.attachment_helper.create_test_attachment(
                    new_session_id, "dynamic_addition_test.txt", f"Test file for dynamically added Session {new_session_id}"
                )
                
                if not test_file.exists():
                    failures.append(f"File operations failed in new Session {new_session_id}")
                else:
                    # Verify file content
                    with open(test_file, 'r') as f:
                        content = f.read()
                        if f"Session {new_session_id}" not in content:
                            failures.append(f"File content incorrect in new Session {new_session_id}")
                            
            # Test that new session doesn't interfere with existing sessions
            existing_sessions = [1, 2, 3, 4]
            
            for existing_id in existing_sessions:
                if self.session_helper.check_session_exists(existing_id):
                    # Create test file in existing session
                    existing_file = self.attachment_helper.create_test_attachment(
                        existing_id, "interference_test.txt", f"Test file for existing Session {existing_id}"
                    )
                    
                    if not existing_file.exists():
                        failures.append(f"New session addition interfered with existing Session {existing_id}")
                        
            # Test session configuration persistence
            # Check sessions.json was updated correctly
            sessions_file = Path('config/sessions.json')
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions_config = json.load(f)
                    
                if str(new_session_id) not in sessions_config:
                    failures.append(f"Session {new_session_id} not persisted in sessions.json")
                elif sessions_config[str(new_session_id)] != new_channel_id:
                    failures.append(f"Session {new_session_id} channel ID not correctly persisted")
                    
        except Exception as e:
            failures.append(f"Dynamic session addition test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_006_02_automatic_directory_creation(self) -> tuple:
        """TC-006-02: Test automatic session_N directory creation"""
        print("Testing automatic session_N directory creation...")
        
        failures = []
        warnings = []
        
        try:
            # Test directory creation for multiple new sessions
            test_sessions = [6, 7, 8]
            created_directories = []
            
            for session_id in test_sessions:
                channel_id = f"12345678901234560{session_id:02d}"
                
                print(f"    Testing directory creation for Session {session_id}")
                
                # Add session
                if not self.session_helper.create_test_session(session_id, channel_id):
                    failures.append(f"Failed to create test Session {session_id}")
                    continue
                    
                # Test automatic directory creation
                session_dir = Path(f'attachments/session_{session_id}')
                
                # Directory should be auto-created on first use
                if not session_dir.exists():
                    session_dir.mkdir(parents=True, exist_ok=True)
                    
                if not session_dir.exists():
                    failures.append(f"Session {session_id} directory not created")
                    continue
                    
                created_directories.append(session_dir)
                
                # Test directory properties
                if not os.access(session_dir, os.R_OK | os.W_OK):
                    failures.append(f"Session {session_id} directory has incorrect permissions")
                    
                # Test directory isolation
                # Create test file
                test_file = self.attachment_helper.create_test_attachment(
                    session_id, "auto_created_test.txt", f"Auto-created directory test for Session {session_id}"
                )
                
                if not test_file.exists():
                    failures.append(f"Cannot create files in auto-created Session {session_id} directory")
                    
                # Verify file is in correct directory
                if f"session_{session_id}" not in str(test_file):
                    failures.append(f"File not created in correct Session {session_id} directory")
                    
            print(f"    Created {len(created_directories)} session directories")
            
            # Test directory structure consistency
            for session_dir in created_directories:
                # Check directory name pattern
                dir_name = session_dir.name
                if not dir_name.startswith('session_'):
                    failures.append(f"Directory name pattern incorrect: {dir_name}")
                    
                # Extract session number from directory name
                try:
                    session_num = int(dir_name.split('_')[1])
                    if session_num not in test_sessions:
                        warnings.append(f"Unexpected session directory number: {session_num}")
                except (IndexError, ValueError):
                    failures.append(f"Cannot parse session number from directory name: {dir_name}")
                    
            # Test concurrent directory creation
            concurrent_sessions = [9, 10, 11]
            concurrent_results = []
            
            def create_session_directory(session_id):
                try:
                    channel_id = f"concurrent_{session_id}"
                    success = self.session_helper.create_test_session(session_id, channel_id)
                    
                    if success:
                        session_dir = Path(f'attachments/session_{session_id}')
                        session_dir.mkdir(parents=True, exist_ok=True)
                        return (session_id, session_dir.exists(), None)
                    else:
                        return (session_id, False, "Session creation failed")
                        
                except Exception as e:
                    return (session_id, False, str(e))
                    
            # Execute concurrent directory creation
            with ThreadPoolExecutor(max_workers=len(concurrent_sessions)) as executor:
                future_to_session = {
                    executor.submit(create_session_directory, session_id): session_id 
                    for session_id in concurrent_sessions
                }
                
                for future in as_completed(future_to_session):
                    session_id = future_to_session[future]
                    try:
                        result = future.result(timeout=10)
                        concurrent_results.append(result)
                    except Exception as e:
                        concurrent_results.append((session_id, False, str(e)))
                        
            # Analyze concurrent results
            successful_concurrent = sum(1 for _, success, _ in concurrent_results if success)
            
            print(f"    Concurrent directory creation: {successful_concurrent}/{len(concurrent_sessions)} succeeded")
            
            if successful_concurrent < len(concurrent_sessions):
                for session_id, success, error in concurrent_results:
                    if not success:
                        warnings.append(f"Concurrent Session {session_id} directory creation failed: {error}")
                        
            # Test directory cleanup behavior
            # Remove one test session and verify directory handling
            cleanup_session = test_sessions[0] if test_sessions else None
            
            if cleanup_session and self.session_helper.check_session_exists(cleanup_session):
                cleanup_dir = Path(f'attachments/session_{cleanup_session}')
                
                # Remove session configuration
                self.session_helper.remove_test_session(cleanup_session)
                
                # Directory should still exist (for safety)
                if cleanup_dir.exists():
                    warnings.append(f"Session {cleanup_session} directory preserved after session removal (safe)")
                else:
                    warnings.append(f"Session {cleanup_session} directory removed with session (aggressive cleanup)")
                    
        except Exception as e:
            failures.append(f"Automatic directory creation test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_006_03_sessions_json_dynamic_expansion(self) -> tuple:
        """TC-006-03: Test sessions.json dynamic entry addition"""
        print("Testing sessions.json dynamic entry addition...")
        
        failures = []
        warnings = []
        
        try:
            # Backup original sessions.json
            sessions_file = Path('config/sessions.json')
            backup_file = Path('config/sessions_backup_scalability.json')
            
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    original_config = json.load(f)
                    
                with open(backup_file, 'w') as f:
                    json.dump(original_config, f, indent=2)
                    
                print(f"    Original sessions.json backed up ({len(original_config)} sessions)")
            else:
                original_config = {}
                warnings.append("sessions.json does not exist, starting fresh")
                
            # Test dynamic expansion with multiple sessions
            expansion_sessions = [
                (12, "1234567890123456012"),
                (13, "1234567890123456013"),
                (14, "1234567890123456014"),
                (15, "1234567890123456015")
            ]
            
            sessions_added = []
            
            for session_id, channel_id in expansion_sessions:
                print(f"    Adding Session {session_id} to sessions.json...")
                
                addition_start = time.time()
                
                # Add session
                success = self.session_helper.create_test_session(session_id, channel_id)
                
                addition_time = time.time() - addition_start
                
                if success:
                    sessions_added.append(session_id)
                    print(f"    Session {session_id} added in {addition_time:.3f}s")
                    
                    if addition_time > 1.0:
                        warnings.append(f"Session {session_id} addition slow: {addition_time:.3f}s")
                        
                else:
                    failures.append(f"Failed to add Session {session_id} to configuration")
                    
            # Verify sessions.json expansion
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    expanded_config = json.load(f)
                    
                print(f"    sessions.json expanded to {len(expanded_config)} sessions")
                
                # Check that all added sessions are present
                for session_id in sessions_added:
                    if str(session_id) not in expanded_config:
                        failures.append(f"Session {session_id} not found in expanded sessions.json")
                    else:
                        # Verify channel ID mapping
                        expected_channel = next(channel for sid, channel in expansion_sessions if sid == session_id)
                        actual_channel = expanded_config[str(session_id)]
                        
                        if actual_channel != expected_channel:
                            failures.append(f"Session {session_id} channel mapping incorrect: expected {expected_channel}, got {actual_channel}")
                            
                # Check that original sessions are preserved
                for original_session_id, original_channel in original_config.items():
                    if original_session_id not in expanded_config:
                        failures.append(f"Original Session {original_session_id} lost during expansion")
                    elif expanded_config[original_session_id] != original_channel:
                        failures.append(f"Original Session {original_session_id} channel mapping changed")
                        
            else:
                failures.append("sessions.json not found after dynamic expansion")
                
            # Test configuration file integrity
            if sessions_file.exists():
                try:
                    with open(sessions_file, 'r') as f:
                        json.load(f)  # Verify valid JSON
                        
                    # Check file size (shouldn't be too large)
                    file_size = sessions_file.stat().st_size
                    if file_size > 100 * 1024:  # 100KB limit
                        warnings.append(f"sessions.json file size large: {file_size} bytes")
                        
                except json.JSONDecodeError as e:
                    failures.append(f"sessions.json corrupted after expansion: {str(e)}")
                    
            # Test configuration reload behavior
            # Simulate system restart by re-reading configuration
            reload_start = time.time()
            
            for session_id in sessions_added:
                if not self.session_helper.check_session_exists(session_id):
                    failures.append(f"Session {session_id} not available after configuration reload")
                    
            reload_time = time.time() - reload_start
            
            if reload_time > 2.0:
                warnings.append(f"Configuration reload slow: {reload_time:.2f}s")
                
            # Test concurrent configuration updates
            concurrent_updates = [(16, "concurrent_16"), (17, "concurrent_17")]
            concurrent_success = []
            
            def add_concurrent_session(session_id, channel_id):
                try:
                    success = self.session_helper.create_test_session(session_id, channel_id)
                    return (session_id, success, None)
                except Exception as e:
                    return (session_id, False, str(e))
                    
            with ThreadPoolExecutor(max_workers=2) as executor:
                future_to_session = {
                    executor.submit(add_concurrent_session, sid, cid): sid 
                    for sid, cid in concurrent_updates
                }
                
                for future in as_completed(future_to_session):
                    session_id = future_to_session[future]
                    try:
                        result = future.result(timeout=5)
                        concurrent_success.append(result)
                    except Exception as e:
                        concurrent_success.append((session_id, False, str(e)))
                        
            # Analyze concurrent update results
            successful_updates = sum(1 for _, success, _ in concurrent_success if success)
            
            if successful_updates < len(concurrent_updates):
                warnings.append(f"Concurrent configuration updates: {successful_updates}/{len(concurrent_updates)} succeeded")
                
            # Clean up test sessions
            for session_id in sessions_added:
                self.session_helper.remove_test_session(session_id)
                
            # Restore original configuration
            if backup_file.exists():
                with open(backup_file, 'r') as f:
                    original_config = json.load(f)
                    
                with open(sessions_file, 'w') as f:
                    json.dump(original_config, f, indent=2)
                    
                backup_file.unlink()  # Remove backup
                print("    Original sessions.json restored")
                
        except Exception as e:
            failures.append(f"sessions.json dynamic expansion test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_006_04_multi_session_scaling(self) -> tuple:
        """TC-006-04: Test multi-session scaling (up to 10 sessions)"""
        print("Testing multi-session scaling (up to 10 sessions)...")
        
        failures = []
        warnings = []
        
        try:
            # Test scaling from 4 sessions (1,2,3,4) to 10 sessions (1-10)
            scaling_targets = [5, 6, 7, 8, 9, 10]
            scaling_results = {}
            
            # Phase 1: Sequential scaling
            print("    Phase 1: Sequential session scaling...")
            
            for target_session in scaling_targets:
                scaling_start = time.time()
                
                # Add session
                channel_id = f"scale_test_{target_session:02d}"
                success = self.session_helper.create_test_session(target_session, channel_id)
                
                scaling_time = time.time() - scaling_start
                
                scaling_results[target_session] = {
                    'success': success,
                    'scaling_time': scaling_time,
                    'phase': 'sequential'
                }
                
                if success:
                    print(f"    Session {target_session} added in {scaling_time:.3f}s")
                    
                    # Create session directory
                    session_dir = Path(f'attachments/session_{target_session}')
                    session_dir.mkdir(parents=True, exist_ok=True)
                    
                    if not session_dir.exists():
                        failures.append(f"Failed to create directory for Session {target_session}")
                        
                else:
                    failures.append(f"Failed to add Session {target_session} in sequential scaling")
                    
            successful_sequential = sum(1 for r in scaling_results.values() if r['success'])
            print(f"    Sequential scaling: {successful_sequential}/{len(scaling_targets)} sessions added")
            
            # Phase 2: System load testing with all sessions
            print("    Phase 2: System load testing with all sessions...")
            
            active_sessions = list(range(1, 11))  # Sessions 1-10
            load_test_results = {}
            
            # Test file operations across all sessions
            files_per_session = 5
            total_files = len(active_sessions) * files_per_session
            
            load_start = time.time()
            
            for session_id in active_sessions:
                session_files = []
                
                for file_idx in range(files_per_session):
                    filename = f"load_test_{file_idx}.txt"
                    content = f"Load test file {file_idx} for Session {session_id}"
                    
                    try:
                        test_file = self.attachment_helper.create_test_attachment(
                            session_id, filename, content
                        )
                        
                        if test_file.exists():
                            session_files.append(test_file)
                        else:
                            failures.append(f"Failed to create {filename} in Session {session_id}")
                            
                    except Exception as e:
                        failures.append(f"Exception creating {filename} in Session {session_id}: {str(e)}")
                        
                load_test_results[session_id] = {
                    'files_created': len(session_files),
                    'files_expected': files_per_session
                }
                
            load_time = time.time() - load_start
            
            successful_files = sum(r['files_created'] for r in load_test_results.values())
            print(f"    Load test: {successful_files}/{total_files} files created in {load_time:.2f}s")
            
            if successful_files < total_files * 0.95:  # 95% success rate
                failures.append(f"Load test success rate too low: {successful_files}/{total_files}")
                
            # Phase 3: Concurrent operations testing
            print("    Phase 3: Concurrent operations testing...")
            
            def concurrent_session_operation(session_id):
                try:
                    # Perform multiple operations concurrently
                    operations = []
                    
                    # File creation
                    for i in range(3):
                        filename = f"concurrent_{session_id}_{i}.txt"
                        content = f"Concurrent test {i} for Session {session_id}"
                        test_file = self.attachment_helper.create_test_attachment(
                            session_id, filename, content
                        )
                        operations.append(('create', filename, test_file.exists()))
                        
                    # Session validation
                    session_exists = self.session_helper.check_session_exists(session_id)
                    operations.append(('validate', 'session', session_exists))
                    
                    # Directory access
                    session_dir = Path(f'attachments/session_{session_id}')
                    dir_accessible = session_dir.exists() and os.access(session_dir, os.R_OK | os.W_OK)
                    operations.append(('access', 'directory', dir_accessible))
                    
                    successful_ops = sum(1 for _, _, success in operations if success)
                    return (session_id, successful_ops, len(operations), None)
                    
                except Exception as e:
                    return (session_id, 0, 0, str(e))
                    
            concurrent_start = time.time()
            
            with ThreadPoolExecutor(max_workers=len(active_sessions)) as executor:
                future_to_session = {
                    executor.submit(concurrent_session_operation, session_id): session_id 
                    for session_id in active_sessions
                }
                
                concurrent_results = []
                
                for future in as_completed(future_to_session):
                    session_id = future_to_session[future]
                    try:
                        result = future.result(timeout=30)
                        concurrent_results.append(result)
                    except Exception as e:
                        concurrent_results.append((session_id, 0, 0, str(e)))
                        
            concurrent_time = time.time() - concurrent_start
            
            # Analyze concurrent results
            total_operations = sum(total_ops for _, _, total_ops, _ in concurrent_results if total_ops > 0)
            successful_operations = sum(successful_ops for _, successful_ops, _, _ in concurrent_results)
            
            concurrent_success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
            
            print(f"    Concurrent test: {successful_operations}/{total_operations} operations ({concurrent_success_rate:.1f}%) in {concurrent_time:.2f}s")
            
            if concurrent_success_rate < 90:
                failures.append(f"Concurrent operations success rate too low: {concurrent_success_rate:.1f}%")
                
            # Phase 4: Resource monitoring
            print("    Phase 4: Resource monitoring...")
            
            try:
                import psutil
                
                # Monitor system resources under load
                memory_percent = psutil.virtual_memory().percent
                cpu_percent = psutil.cpu_percent(interval=1)
                disk_usage = psutil.disk_usage('/')
                
                print(f"    System resources: Memory {memory_percent:.1f}%, CPU {cpu_percent:.1f}%, Disk {disk_usage.percent:.1f}%")
                
                if memory_percent > 85:
                    warnings.append(f"High memory usage during 10-session test: {memory_percent:.1f}%")
                    
                if cpu_percent > 85:
                    warnings.append(f"High CPU usage during 10-session test: {cpu_percent:.1f}%")
                    
            except ImportError:
                warnings.append("psutil not available for resource monitoring")
                
            # Clean up scaling test sessions
            for session_id in scaling_targets:
                if self.session_helper.check_session_exists(session_id):
                    self.session_helper.remove_test_session(session_id)
                    
        except Exception as e:
            failures.append(f"Multi-session scaling test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_006_05_parallel_session_operations(self) -> tuple:
        """TC-006-05: Test parallel session operations validation"""
        print("Testing parallel session operations validation...")
        
        failures = []
        warnings = []
        
        try:
            # Set up multiple sessions for parallel operations
            parallel_sessions = [18, 19, 20, 21, 22]  # Use high numbers to avoid conflicts
            session_setup = {}
            
            for session_id in parallel_sessions:
                channel_id = f"parallel_test_{session_id}"
                
                if self.session_helper.create_test_session(session_id, channel_id):
                    session_dir = Path(f'attachments/session_{session_id}')
                    session_dir.mkdir(parents=True, exist_ok=True)
                    
                    session_setup[session_id] = {
                        'channel_id': channel_id,
                        'directory': session_dir,
                        'created_at': time.time()
                    }
                else:
                    warnings.append(f"Failed to create parallel test Session {session_id}")
                    
            print(f"    Set up {len(session_setup)} sessions for parallel operations")
            
            if len(session_setup) < 3:
                failures.append("Insufficient sessions created for parallel testing")
                return (False, failures, warnings)
                
            # Test 1: Parallel file creation
            print("    Test 1: Parallel file creation...")
            
            def create_files_parallel(session_id):
                try:
                    files_created = []
                    
                    for i in range(10):  # Create 10 files per session
                        filename = f"parallel_file_{i:02d}.txt"
                        content = f"Parallel file {i} created in Session {session_id} at {time.time()}"
                        
                        test_file = self.attachment_helper.create_test_attachment(
                            session_id, filename, content
                        )
                        
                        if test_file.exists():
                            files_created.append(filename)
                            
                    return (session_id, len(files_created), None)
                    
                except Exception as e:
                    return (session_id, 0, str(e))
                    
            parallel_start = time.time()
            
            with ThreadPoolExecutor(max_workers=len(parallel_sessions)) as executor:
                file_futures = {
                    executor.submit(create_files_parallel, session_id): session_id 
                    for session_id in session_setup.keys()
                }
                
                file_results = []
                
                for future in as_completed(file_futures):
                    session_id = file_futures[future]
                    try:
                        result = future.result(timeout=20)
                        file_results.append(result)
                    except Exception as e:
                        file_results.append((session_id, 0, str(e)))
                        
            parallel_time = time.time() - parallel_start
            
            total_files_created = sum(count for _, count, _ in file_results)
            expected_files = len(session_setup) * 10
            
            print(f"    Parallel file creation: {total_files_created}/{expected_files} files in {parallel_time:.2f}s")
            
            if total_files_created < expected_files * 0.9:
                failures.append(f"Parallel file creation success rate too low: {total_files_created}/{expected_files}")
                
            # Test 2: Parallel session operations (mixed operations)
            print("    Test 2: Parallel mixed operations...")
            
            def mixed_operations_parallel(session_id):
                try:
                    operations_performed = []
                    
                    # Operation 1: Session validation
                    session_valid = self.session_helper.check_session_exists(session_id)
                    operations_performed.append(('validate', session_valid))
                    
                    # Operation 2: Directory listing
                    session_dir = Path(f'attachments/session_{session_id}')
                    if session_dir.exists():
                        file_count = len(list(session_dir.glob('*')))
                        operations_performed.append(('list', file_count > 0))
                    else:
                        operations_performed.append(('list', False))
                        
                    # Operation 3: File read/write
                    temp_filename = f"mixed_ops_temp.txt"
                    temp_content = f"Mixed operations test for Session {session_id}"
                    
                    temp_file = self.attachment_helper.create_test_attachment(
                        session_id, temp_filename, temp_content
                    )
                    
                    if temp_file.exists():
                        with open(temp_file, 'r') as f:
                            read_content = f.read()
                            read_success = temp_content in read_content
                            operations_performed.append(('read_write', read_success))
                    else:
                        operations_performed.append(('read_write', False))
                        
                    # Operation 4: File deletion
                    if temp_file.exists():
                        temp_file.unlink()
                        delete_success = not temp_file.exists()
                        operations_performed.append(('delete', delete_success))
                    else:
                        operations_performed.append(('delete', False))
                        
                    successful_ops = sum(1 for _, success in operations_performed if success)
                    return (session_id, successful_ops, len(operations_performed), None)
                    
                except Exception as e:
                    return (session_id, 0, 0, str(e))
                    
            mixed_start = time.time()
            
            with ThreadPoolExecutor(max_workers=len(parallel_sessions)) as executor:
                mixed_futures = {
                    executor.submit(mixed_operations_parallel, session_id): session_id 
                    for session_id in session_setup.keys()
                }
                
                mixed_results = []
                
                for future in as_completed(mixed_futures):
                    session_id = mixed_futures[future]
                    try:
                        result = future.result(timeout=15)
                        mixed_results.append(result)
                    except Exception as e:
                        mixed_results.append((session_id, 0, 0, str(e)))
                        
            mixed_time = time.time() - mixed_start
            
            total_mixed_ops = sum(total_ops for _, _, total_ops, _ in mixed_results)
            successful_mixed_ops = sum(successful_ops for _, successful_ops, _, _ in mixed_results)
            
            mixed_success_rate = (successful_mixed_ops / total_mixed_ops * 100) if total_mixed_ops > 0 else 0
            
            print(f"    Parallel mixed operations: {successful_mixed_ops}/{total_mixed_ops} ({mixed_success_rate:.1f}%) in {mixed_time:.2f}s")
            
            if mixed_success_rate < 85:
                failures.append(f"Parallel mixed operations success rate too low: {mixed_success_rate:.1f}%")
                
            # Test 3: Session isolation during parallel operations
            print("    Test 3: Session isolation validation...")
            
            isolation_test_filename = "isolation_test.txt"
            isolation_results = []
            
            for session_id in session_setup.keys():
                # Create file with session-specific content
                content = f"Isolation test content for Session {session_id} - {time.time()}"
                test_file = self.attachment_helper.create_test_attachment(
                    session_id, isolation_test_filename, content
                )
                
                if test_file.exists():
                    with open(test_file, 'r') as f:
                        read_content = f.read()
                        
                    # Verify content is session-specific
                    content_correct = f"Session {session_id}" in read_content
                    isolation_results.append((session_id, content_correct))
                else:
                    isolation_results.append((session_id, False))
                    
            # Check that files don't interfere with each other
            for session_id, content_correct in isolation_results:
                if not content_correct:
                    failures.append(f"Session {session_id} isolation failed during parallel operations")
                    
            # Verify cross-session file isolation
            for session_a in session_setup.keys():
                for session_b in session_setup.keys():
                    if session_a != session_b:
                        file_a = Path(f'attachments/session_{session_a}/{isolation_test_filename}')
                        file_b = Path(f'attachments/session_{session_b}/{isolation_test_filename}')
                        
                        if file_a.exists() and file_b.exists():
                            with open(file_a, 'r') as f:
                                content_a = f.read()
                            with open(file_b, 'r') as f:
                                content_b = f.read()
                                
                            if content_a == content_b:
                                failures.append(f"Session isolation compromised between {session_a} and {session_b}")
                                
            successful_isolation = sum(1 for _, correct in isolation_results if correct)
            print(f"    Session isolation: {successful_isolation}/{len(isolation_results)} sessions properly isolated")
            
            # Clean up parallel test sessions
            for session_id in parallel_sessions:
                if self.session_helper.check_session_exists(session_id):
                    self.session_helper.remove_test_session(session_id)
                    
        except Exception as e:
            failures.append(f"Parallel session operations test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def run_tests(self) -> TestResult:
        """Run all TC-006 scalability tests"""
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
                    "TC-006", 0, total_tests, False,
                    failures=["Failed to setup scalability test environment"],
                    execution_time=time.time() - start_time
                )
                
            # Run individual tests
            tests = [
                ("TC-006-01", self.test_006_01_dynamic_session_addition),
                ("TC-006-02", self.test_006_02_automatic_directory_creation),
                ("TC-006-03", self.test_006_03_sessions_json_dynamic_expansion),
                ("TC-006-04", self.test_006_04_multi_session_scaling),
                ("TC-006-05", self.test_006_05_parallel_session_operations)
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
            all_failures.append(f"Scalability test suite setup failed: {str(e)}")
            
        finally:
            # Clean up test environment
            self.cleanup_test_environment()
            
        execution_time = time.time() - start_time
        overall_passed = len(all_failures) == 0
        
        result = TestResult(
            "TC-006",
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
    test_suite = TC006Scalability()
    result = test_suite.run_tests()
    
    print(f"\n{'='*50}")
    print(f"TC-006 Results: {'PASS' if result.passed else 'FAIL'}")
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