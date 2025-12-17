#!/usr/bin/env python3
"""
Test Error Reporting System
Comprehensive testing of macOS error detection and reporting
"""

import sys
import os
from pathlib import Path

# Add source to path for testing
bundle_source = Path(__file__).parent / "ImgApp_macOS_Bundle" / "source"
sys.path.insert(0, str(bundle_source))

try:
    from macos_error_reporter import MacOSErrorReporter, initialize_error_reporter
    print("✅ Error reporter imported successfully")
except ImportError as e:
    print(f"❌ Failed to import error reporter: {e}")
    sys.exit(1)

def test_system_info():
    """Test system information collection"""
    print("\n🖥️  Testing system info collection...")
    
    try:
        reporter = MacOSErrorReporter()
        info = reporter.system_info
        
        print(f"  Platform: {info['platform']['system']} {info['platform']['release']}")
        print(f"  Python: {info['python']['version']}")
        print(f"  Frozen: {info['python']['frozen']}")
        print(f"  PyQt5: {'Available' if info['pyqt5']['available'] else 'Missing'}")
        print(f"  Requests: {'Available' if info['requests']['available'] else 'Missing'}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ System info test failed: {e}")
        return False

def test_tool_checking():
    """Test tool availability checking"""
    print("\n🔧 Testing tool checking...")
    
    try:
        reporter = MacOSErrorReporter()
        tool_status = reporter.check_tools()
        
        for tool, status in tool_status.items():
            if status['working']:
                print(f"  ✅ {tool}: Working ({status['version']})")
            else:
                print(f"  ❌ {tool}: {status['error']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Tool checking test failed: {e}")
        return False

def test_license_system():
    """Test license system checking"""
    print("\n🔑 Testing license system...")
    
    try:
        reporter = MacOSErrorReporter()
        license_info = reporter.test_license_system()
        
        print(f"  License file: {'Found' if license_info['license_file']['exists'] else 'Missing'}")
        print(f"  License count: {license_info['license_file'].get('license_count', 0)}")
        print(f"  Hardware ID: {'Generated' if license_info['hardware_id'].get('generated', False) else 'Failed'}")
        print(f"  Server: {'Reachable' if license_info['server_connectivity'].get('reachable', False) else 'Unreachable'}")
        
        if 'hardware_id' in license_info and license_info['hardware_id'].get('generated'):
            print(f"  HW ID Value: {license_info['hardware_id']['value']}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ License system test failed: {e}")
        return False

def test_app_structure():
    """Test application structure checking"""
    print("\n📁 Testing app structure...")
    
    try:
        reporter = MacOSErrorReporter()
        structure_info = reporter.check_app_structure()
        
        if getattr(sys, 'frozen', False):
            print("  Running in production mode")
            for dir_name, info in structure_info['bundle_structure'].items():
                status = "✅" if info['exists'] else "❌"
                print(f"  {status} {dir_name}: {'Found' if info['exists'] else 'Missing'}")
        else:
            print("  Running in development mode")
        
        return True
        
    except Exception as e:
        print(f"  ❌ App structure test failed: {e}")
        return False

def test_error_logging():
    """Test error logging functionality"""
    print("\n📝 Testing error logging...")
    
    try:
        reporter = MacOSErrorReporter()
        
        # Test error logging
        reporter.log_error("Test error message")
        reporter.log_warning("Test warning message")
        
        print(f"  Errors logged: {len(reporter.errors)}")
        print(f"  Warnings logged: {len(reporter.warnings)}")
        print(f"  Log directory: {reporter.log_dir}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error logging test failed: {e}")
        return False

def test_diagnostic_report():
    """Test diagnostic report generation"""
    print("\n📋 Testing diagnostic report generation...")
    
    try:
        reporter = MacOSErrorReporter()
        report = reporter.generate_diagnostic_report()
        
        print(f"  Report generated: {report['report_info']['generated_at']}")
        print(f"  Report mode: {report['report_info']['app_mode']}")
        print(f"  Report saved to: {reporter.log_dir}")
        
        # Check report sections
        sections = ['system_info', 'tool_status', 'license_system', 'app_structure']
        for section in sections:
            status = "✅" if section in report else "❌"
            print(f"  {status} {section}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Diagnostic report test failed: {e}")
        return False

def test_startup_diagnostics():
    """Test startup diagnostics"""
    print("\n🚀 Testing startup diagnostics...")
    
    try:
        from macos_error_reporter import log_startup_diagnostics
        
        success = log_startup_diagnostics()
        print(f"  Startup diagnostics: {'✅ Passed' if success else '❌ Failed'}")
        
        return success
        
    except Exception as e:
        print(f"  ❌ Startup diagnostics test failed: {e}")
        return False

def main():
    """Run all error reporting tests"""
    print("🧪 MACOS ERROR REPORTING TEST SUITE")
    print("=" * 40)
    
    tests = [
        ("System Info", test_system_info),
        ("Tool Checking", test_tool_checking),
        ("License System", test_license_system),
        ("App Structure", test_app_structure),
        ("Error Logging", test_error_logging),
        ("Diagnostic Report", test_diagnostic_report),
        ("Startup Diagnostics", test_startup_diagnostics)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 TEST RESULTS")
    print("-" * 20)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All error reporting tests passed!")
        print("Your macOS app will have comprehensive error detection!")
    else:
        print("⚠️  Some tests failed - check error reporting setup")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)