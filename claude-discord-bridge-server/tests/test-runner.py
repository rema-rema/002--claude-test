#!/usr/bin/env python3
"""
Multi-Session Test Automation Framework
Main Test Runner for Claude-Discord-Bridge Multi-Session Support

Tests: TC-001 through TC-006 (Success Criteria SC-001 through SC-006)
"""

import sys
import os
import json
import time
import argparse
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from test_utils import TestFramework, TestResult, TestReporter, validate_test_environment, get_test_channel_ids
from tc001_basic_functionality import TC001BasicFunctionality
from tc002_file_management import TC002FileManagement  
from tc003_session_management import TC003SessionManagement
from tc004_recovery_error import TC004RecoveryError
from tc005_performance import TC005Performance
from tc006_scalability import TC006Scalability

class MultiSessionTestRunner:
    """Multi-Session Test Suite Main Runner"""
    
    def __init__(self):
        self.framework = TestFramework()
        self.reporter = TestReporter()
        self.test_suites = {
            'TC-001': TC001BasicFunctionality(),
            'TC-002': TC002FileManagement(),
            'TC-003': TC003SessionManagement(),
            'TC-004': TC004RecoveryError(),
            'TC-005': TC005Performance(),
            'TC-006': TC006Scalability()
        }
        self.results = {}
        
    def setup_test_environment(self):
        """テスト環境のセットアップ"""
        print("🔧 Setting up test environment...")
        
        # Validate environment variables first
        env_valid, env_message = validate_test_environment()
        if not env_valid:
            print(f"❌ Environment validation failed: {env_message}")
            print("📝 To fix this:")
            print("   1. Edit .env file in project root")
            print("   2. Set CC_DISCORD_CHANNEL_ID_002_B=<channel_B_id>")
            print("   3. Set CC_DISCORD_CHANNEL_ID_002_C=<channel_C_id>")
            print("   4. Re-run tests")
            return False
            
        print(f"✅ Environment validation: {env_message}")
        
        # Display channel configuration
        channel_ids = get_test_channel_ids()
        print("📋 Test Channel Configuration:")
        for session_id, channel_id in channel_ids.items():
            if session_id in [1, 2, 3, 4]:
                session_name = {1: "Default", 2: "Channel A", 3: "Channel B", 4: "Channel C"}[session_id]
                print(f"   Session {session_id} ({session_name}): {channel_id}")
        
        # Test directory creation
        os.makedirs('tests/temp', exist_ok=True)
        os.makedirs('tests/logs', exist_ok=True)
        os.makedirs('tests/reports', exist_ok=True)
        
        # Backup current sessions.json
        sessions_file = Path('config/sessions.json')
        if sessions_file.exists():
            backup_file = f'tests/temp/sessions_backup_{int(time.time())}.json'
            subprocess.run(['cp', str(sessions_file), backup_file])
            print(f"✅ Backed up sessions.json to {backup_file}")
        
        return True
        
    def cleanup_test_environment(self):
        """テスト環境のクリーンアップ"""
        print("🧹 Cleaning up test environment...")
        
        # Restore sessions.json if backup exists
        backup_files = list(Path('tests/temp').glob('sessions_backup_*.json'))
        if backup_files:
            latest_backup = max(backup_files, key=lambda p: p.stat().st_mtime)
            subprocess.run(['cp', str(latest_backup), 'config/sessions.json'])
            print(f"✅ Restored sessions.json from {latest_backup}")
        
        # Clean temporary test files
        subprocess.run(['rm', '-rf', 'tests/temp/test_*'], check=False)
        
        return True
        
    def run_suite(self, suite_name):
        """個別テストスイートの実行"""
        if suite_name not in self.test_suites:
            raise ValueError(f"Unknown test suite: {suite_name}")
            
        print(f"🚀 Running {suite_name}: {self.test_suites[suite_name].name}")
        start_time = time.time()
        
        try:
            result = self.test_suites[suite_name].run_tests()
            result.execution_time = time.time() - start_time
            result.suite_name = suite_name
            
            self.results[suite_name] = result
            
            # Print immediate results
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"{status} {suite_name}: {result.passed_tests}/{result.total_tests} tests passed")
            
            if result.failures:
                for failure in result.failures:
                    print(f"  ❌ {failure}")
                    
            if result.warnings:
                for warning in result.warnings:
                    print(f"  ⚠️  {warning}")
                    
            return result
            
        except Exception as e:
            result = TestResult(suite_name, 0, 1, False)
            result.failures = [f"Suite execution failed: {str(e)}"]
            result.execution_time = time.time() - start_time
            self.results[suite_name] = result
            print(f"❌ FAIL {suite_name}: Suite execution failed - {str(e)}")
            return result
            
    def run_all_suites(self, skip_long_tests=False):
        """全テストスイートの実行"""
        print("🎯 Running all test suites...")
        
        # Order tests by dependency and execution time
        test_order = ['TC-001', 'TC-002', 'TC-003', 'TC-004', 'TC-005']
        if not skip_long_tests:
            test_order.append('TC-006')
            
        for suite_name in test_order:
            print(f"\n{'='*60}")
            result = self.run_suite(suite_name)
            
            # Stop on critical failures for dependent tests
            if not result.passed and suite_name in ['TC-001', 'TC-002']:
                print(f"⚠️  Critical failure in {suite_name}, stopping execution")
                break
                
    def generate_comprehensive_report(self):
        """総合テストレポートの生成"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'tests/reports/test_report_{timestamp}.html'
        
        total_tests = sum(r.total_tests for r in self.results.values())
        passed_tests = sum(r.passed_tests for r in self.results.values())
        total_time = sum(r.execution_time for r in self.results.values())
        
        # Success Criteria mapping
        sc_mapping = {
            'TC-001': 'SC-001: 基本機能',
            'TC-002': 'SC-002: セキュリティ・復旧機能',
            'TC-003': 'SC-004: 運用性・安定性',
            'TC-004': 'SC-002: セキュリティ・復旧機能',
            'TC-005': 'SC-003: パフォーマンス・リソース管理', 
            'TC-006': 'SC-006: 拡張性検証'
        }
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Multi-Session Test Report - {timestamp}</title>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; }}
        .summary {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .test-suite {{ margin: 20px 0; border: 1px solid #dee2e6; border-radius: 8px; }}
        .suite-header {{ background: #e9ecef; padding: 15px; font-weight: bold; }}
        .suite-passed {{ background: #d1edcc; }}
        .suite-failed {{ background: #f8c2c2; }}
        .test-details {{ padding: 15px; }}
        .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
        .pass {{ color: #28a745; }}
        .fail {{ color: #dc3545; }}
        .warn {{ color: #ffc107; }}
        .sc-mapping {{ background: #e3f2fd; padding: 10px; border-left: 4px solid #2196f3; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🧪 Multi-Session Test Report</h1>
        <p>Claude-Discord-Bridge Multi-Session Support Validation</p>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div class="summary">
        <h2>📊 Test Summary</h2>
        <div class="metric"><strong>Total Tests:</strong> {total_tests}</div>
        <div class="metric"><strong>Passed:</strong> <span class="pass">{passed_tests}</span></div>
        <div class="metric"><strong>Failed:</strong> <span class="fail">{total_tests - passed_tests}</span></div>
        <div class="metric"><strong>Success Rate:</strong> {(passed_tests/total_tests*100):.1f}%</div>
        <div class="metric"><strong>Total Time:</strong> {total_time:.2f}s</div>
    </div>
"""
        
        # Individual suite results
        for suite_name, result in self.results.items():
            status_class = 'suite-passed' if result.passed else 'suite-failed'
            status_icon = '✅' if result.passed else '❌'
            
            html_content += f"""
    <div class="test-suite">
        <div class="suite-header {status_class}">
            {status_icon} {suite_name}: {self.test_suites[suite_name].name}
        </div>
        <div class="test-details">
            <div class="sc-mapping">
                <strong>Success Criteria:</strong> {sc_mapping.get(suite_name, 'N/A')}
            </div>
            <div class="metric"><strong>Tests:</strong> {result.passed_tests}/{result.total_tests}</div>
            <div class="metric"><strong>Time:</strong> {result.execution_time:.2f}s</div>
"""
            
            if result.failures:
                html_content += "<h4 class='fail'>❌ Failures:</h4><ul>"
                for failure in result.failures:
                    html_content += f"<li class='fail'>{failure}</li>"
                html_content += "</ul>"
                
            if result.warnings:
                html_content += "<h4 class='warn'>⚠️ Warnings:</h4><ul>"
                for warning in result.warnings:
                    html_content += f"<li class='warn'>{warning}</li>"
                html_content += "</ul>"
                
            if hasattr(result, 'metrics') and result.metrics:
                html_content += "<h4>📈 Performance Metrics:</h4><ul>"
                for key, value in result.metrics.items():
                    html_content += f"<li><strong>{key}:</strong> {value}</li>"
                html_content += "</ul>"
                
            html_content += "</div></div>"
            
        html_content += """
</body>
</html>
"""
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        print(f"📄 Comprehensive report generated: {report_file}")
        
        # Also generate JSON report for programmatic access
        json_report = {
            'timestamp': timestamp,
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'total_time': total_time
            },
            'suites': {}
        }
        
        for suite_name, result in self.results.items():
            json_report['suites'][suite_name] = {
                'name': self.test_suites[suite_name].name,
                'passed': result.passed,
                'total_tests': result.total_tests,
                'passed_tests': result.passed_tests,
                'execution_time': result.execution_time,
                'failures': result.failures,
                'warnings': result.warnings,
                'success_criteria': sc_mapping.get(suite_name, 'N/A')
            }
            
        json_file = f'tests/reports/test_report_{timestamp}.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, indent=2, ensure_ascii=False)
            
        print(f"📄 JSON report generated: {json_file}")
        return report_file, json_file
        
    def print_final_summary(self):
        """最終サマリーの表示"""
        print(f"\n{'='*80}")
        print("🎯 FINAL TEST SUMMARY")
        print(f"{'='*80}")
        
        total_tests = sum(r.total_tests for r in self.results.values())
        passed_tests = sum(r.passed_tests for r in self.results.values())
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Success Criteria evaluation
        print(f"\n🎯 SUCCESS CRITERIA EVALUATION:")
        sc_status = {
            'SC-001': any(r.passed for suite, r in self.results.items() if suite == 'TC-001'),
            'SC-002': any(r.passed for suite, r in self.results.items() if suite in ['TC-002', 'TC-004']),
            'SC-003': any(r.passed for suite, r in self.results.items() if suite == 'TC-005'),
            'SC-004': any(r.passed for suite, r in self.results.items() if suite == 'TC-003'),
            'SC-006': any(r.passed for suite, r in self.results.items() if suite == 'TC-006')
        }
        
        for sc, passed in sc_status.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} {sc}")
            
        # Overall assessment
        critical_passed = sc_status['SC-001'] and sc_status['SC-004']  # Basic + Operational
        
        if success_rate >= 90 and critical_passed:
            print(f"\n🎉 OVERALL RESULT: ✅ EXCELLENT - Multi-session implementation ready for production")
        elif success_rate >= 80 and critical_passed:
            print(f"\n✅ OVERALL RESULT: ✅ GOOD - Multi-session implementation ready with minor issues")
        elif success_rate >= 70:
            print(f"\n⚠️  OVERALL RESULT: ⚠️  ACCEPTABLE - Multi-session needs improvements before production")
        else:
            print(f"\n❌ OVERALL RESULT: ❌ NEEDS WORK - Major issues prevent production deployment")

def main():
    parser = argparse.ArgumentParser(description='Multi-Session Test Runner')
    parser.add_argument('--all', action='store_true', help='Run all test suites')
    parser.add_argument('--suite', type=str, help='Run specific test suite (TC-001, TC-002, etc.)')
    parser.add_argument('--quick', action='store_true', help='Skip long-running tests')
    parser.add_argument('--performance-only', action='store_true', help='Run only performance tests')
    parser.add_argument('--report-only', action='store_true', help='Generate report from existing results')
    
    args = parser.parse_args()
    
    runner = MultiSessionTestRunner()
    
    if args.report_only:
        if runner.results:
            runner.generate_comprehensive_report()
        else:
            print("❌ No test results found. Run tests first.")
        return
        
    try:
        # Setup test environment
        if not runner.setup_test_environment():
            print("❌ Failed to setup test environment")
            sys.exit(1)
            
        # Run tests based on arguments
        if args.performance_only:
            runner.run_suite('TC-005')
        elif args.suite:
            runner.run_suite(args.suite.upper())
        elif args.all:
            runner.run_all_suites(skip_long_tests=args.quick)
        else:
            # Default: run critical tests
            for suite in ['TC-001', 'TC-002', 'TC-003']:
                runner.run_suite(suite)
                
        # Generate reports and summary
        if runner.results:
            runner.generate_comprehensive_report()
            runner.print_final_summary()
        else:
            print("⚠️  No tests were executed")
            
    except KeyboardInterrupt:
        print("\n⚠️  Test execution interrupted by user")
    except Exception as e:
        print(f"❌ Test runner failed: {str(e)}")
        sys.exit(1)
    finally:
        runner.cleanup_test_environment()

if __name__ == "__main__":
    main()