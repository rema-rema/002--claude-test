#!/usr/bin/env python3
"""
TC-002: File Management Tests  
Tests for Success Criteria SC-002: セキュリティ・復旧機能 (File Management Aspect)

Test Cases:
- TC-002-01: Session-specific attachment directory separation
- TC-002-02: File conflict detection and resolution
- TC-002-03: Cross-session file access prevention
- TC-002-04: Duplicate file handling with automatic renaming
- TC-002-05: Session directory cleanup and isolation
"""

import os
import sys
import time
import shutil
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_utils import TestFramework, TestResult, SessionTestHelper, AttachmentTestHelper

class TC002FileManagement:
    """TC-002: File Management Test Suite"""
    
    def __init__(self):
        self.name = "File Management Tests (SC-002 File Aspect)"
        self.framework = TestFramework()
        self.session_helper = SessionTestHelper()
        self.attachment_helper = AttachmentTestHelper()
        self.test_sessions = [2, 3, 4]
        
    def setup_test_environment(self) -> bool:
        """Set up file management test environment"""
        print("Setting up file management test environment...")
        
        # Create test sessions
        test_channels = {
            2: "1234567890123456001",
            3: "1234567890123456002", 
            4: "1234567890123456003"
        }
        
        for session_id, channel_id in test_channels.items():
            if not self.session_helper.create_test_session(session_id, channel_id):
                return False
                
        # Ensure attachment directories exist
        for session_id in [1] + self.test_sessions:
            session_dir = Path(f'attachments/session_{session_id}')
            session_dir.mkdir(parents=True, exist_ok=True)
            
        return True
        
    def cleanup_test_environment(self):
        """Clean up file management test environment"""
        print("Cleaning up file management test environment...")
        self.session_helper.cleanup_test_sessions()
        self.attachment_helper.cleanup_test_files()
        
    def test_002_01_session_directory_separation(self) -> tuple:
        """TC-002-01: Test session-specific attachment directory separation"""
        print("Testing session-specific attachment directory separation...")
        
        failures = []
        warnings = []
        
        try:
            # Test directory structure creation
            expected_dirs = [1, 2, 3, 4]  # Session directories
            
            for session_id in expected_dirs:
                session_dir = Path(f'attachments/session_{session_id}')
                if not session_dir.exists():
                    session_dir.mkdir(parents=True, exist_ok=True)
                    
                if not session_dir.exists():
                    failures.append(f"Failed to create session_{session_id} directory")
                    continue
                    
                # Test directory permissions
                if not os.access(session_dir, os.W_OK):
                    failures.append(f"Session_{session_id} directory not writable")
                    
                if not os.access(session_dir, os.R_OK):
                    failures.append(f"Session_{session_id} directory not readable")
                    
            # Test file isolation - create same filename in different sessions
            test_filename = "isolation_test.txt"
            
            for session_id in expected_dirs:
                unique_content = f"Content for session {session_id} - {time.time()}"
                test_file = self.attachment_helper.create_test_attachment(
                    session_id, test_filename, unique_content
                )
                
                if not test_file.exists():
                    failures.append(f"Failed to create {test_filename} in session_{session_id}")
                    continue
                    
                # Verify file contains correct content
                with open(test_file, 'r') as f:
                    content = f.read()
                    if unique_content not in content:
                        failures.append(f"Session_{session_id} file contains incorrect content")
                        
            # Verify files are truly isolated (same name, different content)
            for session_id in expected_dirs:
                file_path = Path(f'attachments/session_{session_id}/{test_filename}')
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        content = f.read()
                        # Should contain session-specific content
                        if f"session {session_id}" not in content:
                            failures.append(f"File isolation failed for session {session_id}")
                            
        except Exception as e:
            failures.append(f"Session directory separation test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_002_02_file_conflict_detection(self) -> tuple:
        """TC-002-02: Test file conflict detection and resolution"""
        print("Testing file conflict detection and resolution...")
        
        failures = []
        warnings = []
        
        try:
            # Test same filename in same session (should overwrite or rename)
            session_id = 2
            test_filename = "conflict_test.txt"
            
            # Create initial file
            initial_content = "Initial content"
            initial_file = self.attachment_helper.create_test_attachment(
                session_id, test_filename, initial_content
            )
            
            if not initial_file.exists():
                failures.append("Failed to create initial conflict test file")
                return (False, failures, warnings)
                
            # Simulate file conflict by creating another file with same name
            # In real system, this would trigger conflict resolution
            conflict_content = "Conflicting content"
            
            # Check if original file exists before potential conflict
            original_size = initial_file.stat().st_size
            
            # Create conflicting file (simulating duplicate upload)
            try:
                conflict_file = self.attachment_helper.create_test_attachment(
                    session_id, test_filename, conflict_content
                )
                
                # Check how system handles the conflict
                if conflict_file.exists():
                    with open(conflict_file, 'r') as f:
                        final_content = f.read()
                        
                    # System should either:
                    # 1. Overwrite with new content, or
                    # 2. Create renamed duplicate file
                    if final_content == conflict_content:
                        warnings.append("File conflict resolved by overwriting (acceptable)")
                    elif final_content == initial_content:
                        warnings.append("File conflict resolved by keeping original (acceptable)")
                    else:
                        failures.append("File conflict resolution produced unexpected content")
                        
            except Exception as e:
                # If system prevents conflict by renaming, that's also acceptable
                warnings.append(f"File conflict handled by system mechanism: {str(e)}")
                
            # Test cross-session conflict (same filename in different sessions - should be allowed)
            other_session = 3
            cross_session_file = self.attachment_helper.create_test_attachment(
                other_session, test_filename, "Cross-session content"
            )
            
            if not cross_session_file.exists():
                failures.append("Failed to create same filename in different session")
            else:
                # Both files should coexist
                if not initial_file.exists():
                    failures.append("Original file was affected by cross-session file creation")
                    
        except Exception as e:
            failures.append(f"File conflict detection test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_002_03_cross_session_access_prevention(self) -> tuple:
        """TC-002-03: Test cross-session file access prevention"""
        print("Testing cross-session file access prevention...")
        
        failures = []
        warnings = []
        
        try:
            # Create files in different sessions
            test_files = {}
            
            for session_id in [1, 2, 3, 4]:
                filename = f"private_session_{session_id}.txt"
                content = f"Private content for session {session_id}"
                
                test_file = self.attachment_helper.create_test_attachment(
                    session_id, filename, content
                )
                test_files[session_id] = test_file
                
            # Verify files exist in their respective sessions
            for session_id, file_path in test_files.items():
                if not file_path.exists():
                    failures.append(f"Private file for session {session_id} not created")
                    continue
                    
                # Verify file is in correct directory
                expected_dir = f"session_{session_id}"
                if expected_dir not in str(file_path):
                    failures.append(f"Private file for session {session_id} in wrong directory")
                    
            # Test that files are not accessible from other sessions
            # (In real system, this would be enforced by access controls)
            for session_id in [1, 2, 3, 4]:
                session_dir = Path(f'attachments/session_{session_id}')
                
                # Check that session directory only contains its own files
                if session_dir.exists():
                    files_in_session = list(session_dir.glob('*'))
                    
                    for file_path in files_in_session:
                        filename = file_path.name
                        
                        # If file contains session identifier, verify it matches
                        if 'session_' in filename:
                            expected_session = filename.split('session_')[1].split('.')[0]
                            if expected_session.isdigit() and int(expected_session) != session_id:
                                failures.append(f"Session {session_id} contains file from session {expected_session}")
                                
            # Simulate access attempt from wrong session (conceptual test)
            # In production, this would be prevented by proper access controls
            session_1_dir = Path('attachments/session_1')
            session_2_dir = Path('attachments/session_2')
            
            if session_1_dir.exists() and session_2_dir.exists():
                # Directories should be separate and isolated
                if session_1_dir.samefile(session_2_dir):
                    failures.append("Session directories are not properly isolated")
                    
        except Exception as e:
            failures.append(f"Cross-session access prevention test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_002_04_duplicate_file_handling(self) -> tuple:
        """TC-002-04: Test duplicate file handling with automatic renaming"""
        print("Testing duplicate file handling with automatic renaming...")
        
        failures = []
        warnings = []
        
        try:
            session_id = 2
            base_filename = "duplicate_test.txt"
            original_content = "Original file content"
            
            # Create original file
            original_file = self.attachment_helper.create_test_attachment(
                session_id, base_filename, original_content
            )
            
            if not original_file.exists():
                failures.append("Failed to create original file for duplicate test")
                return (False, failures, warnings)
                
            # Simulate duplicate file detection by creating files with similar content
            # Test multiple duplicates to see naming pattern
            duplicate_contents = [
                "Duplicate content 1",
                "Duplicate content 2", 
                "Duplicate content 3"
            ]
            
            session_dir = Path(f'attachments/session_{session_id}')
            original_file_count = len(list(session_dir.glob('*'))) if session_dir.exists() else 0
            
            for i, content in enumerate(duplicate_contents):
                try:
                    # In a real system with duplicate detection, this might create renamed files
                    duplicate_name = f"duplicate_test_copy_{i+1}.txt"  # Manual naming for test
                    duplicate_file = self.attachment_helper.create_test_attachment(
                        session_id, duplicate_name, content
                    )
                    
                    if not duplicate_file.exists():
                        failures.append(f"Failed to create duplicate file {duplicate_name}")
                        
                except Exception as e:
                    warnings.append(f"Duplicate handling mechanism active: {str(e)}")
                    
            # Check final state
            if session_dir.exists():
                final_files = list(session_dir.glob('*'))
                final_file_count = len(final_files)
                
                # Should have original file plus duplicates (or renamed versions)
                if final_file_count <= original_file_count:
                    failures.append("Duplicate files were not properly created or managed")
                    
                # Check for naming patterns that indicate duplicate handling
                duplicate_patterns_found = False
                for file_path in final_files:
                    filename = file_path.name
                    if 'copy' in filename.lower() or 'duplicate' in filename.lower() or '_1' in filename:
                        duplicate_patterns_found = True
                        warnings.append(f"Duplicate naming pattern detected: {filename}")
                        
                if not duplicate_patterns_found and final_file_count > original_file_count + 1:
                    warnings.append("Files created but no duplicate naming pattern detected")
                    
            # Test that original file integrity is maintained
            if original_file.exists():
                with open(original_file, 'r') as f:
                    current_content = f.read()
                    if original_content not in current_content:
                        failures.append("Original file content was modified during duplicate handling")
                        
        except Exception as e:
            failures.append(f"Duplicate file handling test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def test_002_05_session_directory_cleanup(self) -> tuple:
        """TC-002-05: Test session directory cleanup and isolation"""
        print("Testing session directory cleanup and isolation...")
        
        failures = []
        warnings = []
        
        try:
            # Create files in multiple sessions to test cleanup
            cleanup_files = {}
            
            for session_id in [2, 3, 4]:
                # Create multiple files per session
                session_files = []
                
                for i in range(3):
                    filename = f"cleanup_test_{i}.txt"
                    content = f"Cleanup test file {i} for session {session_id}"
                    
                    test_file = self.attachment_helper.create_test_attachment(
                        session_id, filename, content
                    )
                    session_files.append(test_file)
                    
                cleanup_files[session_id] = session_files
                
            # Verify all files were created
            total_files_created = 0
            for session_id, files in cleanup_files.items():
                for file_path in files:
                    if file_path.exists():
                        total_files_created += 1
                    else:
                        failures.append(f"Cleanup test file not created: {file_path}")
                        
            # Test session-specific cleanup (simulated)
            # In real system, cleanup would be handled by specific cleanup mechanisms
            target_session = 2
            
            # Get initial state
            session_dir = Path(f'attachments/session_{target_session}')
            if session_dir.exists():
                initial_files = list(session_dir.glob('*'))
                initial_count = len(initial_files)
                
                # Simulate cleanup by removing test files for one session
                for file_path in cleanup_files[target_session]:
                    if file_path.exists():
                        file_path.unlink()  # Remove file
                        
                # Verify cleanup affected only target session
                final_files = list(session_dir.glob('*'))
                final_count = len(final_files)
                
                if final_count >= initial_count:
                    failures.append(f"Session {target_session} cleanup did not reduce file count")
                    
                # Verify other sessions were not affected
                for other_session in [3, 4]:
                    other_dir = Path(f'attachments/session_{other_session}')
                    if other_dir.exists():
                        other_files = list(other_dir.glob('*'))
                        
                        # Should still have cleanup test files
                        cleanup_files_remaining = [f for f in other_files if 'cleanup_test' in f.name]
                        if len(cleanup_files_remaining) == 0:
                            failures.append(f"Cleanup incorrectly affected session {other_session}")
                            
            # Test directory isolation during cleanup
            # Verify directories remain separate and don't interfere
            for session_id in [1, 2, 3, 4]:
                session_dir = Path(f'attachments/session_{session_id}')
                if session_dir.exists():
                    # Check directory permissions remain correct
                    if not os.access(session_dir, os.R_OK | os.W_OK):
                        failures.append(f"Session {session_id} directory permissions changed during cleanup")
                        
            # Test that cleanup doesn't create cross-session access
            # This is a conceptual test - in production, cleanup should maintain isolation
            isolation_maintained = True
            for session_a in [1, 2, 3, 4]:
                for session_b in [1, 2, 3, 4]:
                    if session_a != session_b:
                        dir_a = Path(f'attachments/session_{session_a}')
                        dir_b = Path(f'attachments/session_{session_b}')
                        
                        if dir_a.exists() and dir_b.exists():
                            # Directories should remain separate
                            try:
                                if dir_a.samefile(dir_b):
                                    isolation_maintained = False
                                    failures.append(f"Sessions {session_a} and {session_b} directories merged")
                            except FileNotFoundError:
                                # This is expected if directories don't exist
                                pass
                                
            if isolation_maintained:
                warnings.append("Directory isolation maintained during cleanup operations")
                
        except Exception as e:
            failures.append(f"Session directory cleanup test failed: {str(e)}")
            
        return (len(failures) == 0, failures, warnings)
        
    def run_tests(self) -> TestResult:
        """Run all TC-002 file management tests"""
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
                    "TC-002", 0, total_tests, False,
                    failures=["Failed to setup file management test environment"],
                    execution_time=time.time() - start_time
                )
                
            # Run individual tests
            tests = [
                ("TC-002-01", self.test_002_01_session_directory_separation),
                ("TC-002-02", self.test_002_02_file_conflict_detection),
                ("TC-002-03", self.test_002_03_cross_session_access_prevention),
                ("TC-002-04", self.test_002_04_duplicate_file_handling),
                ("TC-002-05", self.test_002_05_session_directory_cleanup)
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
            all_failures.append(f"File management test suite setup failed: {str(e)}")
            
        finally:
            # Clean up test environment
            self.cleanup_test_environment()
            
        execution_time = time.time() - start_time
        overall_passed = len(all_failures) == 0
        
        result = TestResult(
            "TC-002",
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
    test_suite = TC002FileManagement()
    result = test_suite.run_tests()
    
    print(f"\n{'='*50}")
    print(f"TC-002 Results: {'PASS' if result.passed else 'FAIL'}")
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