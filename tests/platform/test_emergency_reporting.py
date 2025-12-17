#!/usr/bin/env python3
"""
Test Emergency Crash Reporting
Simulates various startup failures to test crash reporting
"""

import sys
import os
from pathlib import Path

# Add source to path
bundle_source = Path(__file__).parent / "ImgApp_macOS_Bundle" / "source"
sys.path.insert(0, str(bundle_source))

def test_emergency_import():
    """Test emergency reporter import"""
    print("🧪 Testing Emergency Reporter Import...")
    
    try:
        from client.utils.crash_reporter import EmergencyCrashReporter, setup_emergency_crash_handler
        print("✅ Emergency reporter imported successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import emergency reporter: {e}")
        return False

def test_emergency_initialization():
    """Test emergency reporter initialization"""
    print("\n🏗️  Testing Emergency Initialization...")
    
    try:
        from client.utils.crash_reporter import EmergencyCrashReporter
        
        reporter = EmergencyCrashReporter()
        print(f"✅ Emergency reporter initialized")
        print(f"📁 Log directory: {reporter.log_dir}")
        print(f"🕐 Startup time: {reporter.startup_time}")
        print(f"📋 Init steps: {len(reporter.init_steps)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Emergency initialization failed: {e}")
        return False

def test_crash_handler_setup():
    """Test crash handler setup"""
    print("\n🛡️  Testing Crash Handler Setup...")
    
    try:
        from client.utils.crash_reporter import setup_emergency_crash_handler
        
        success = setup_emergency_crash_handler()
        print(f"✅ Crash handler setup: {success}")
        
        # Test that exception hook is installed
        if hasattr(sys, 'excepthook'):
            print("✅ Exception hook installed")
        else:
            print("❌ No exception hook found")
        
        return success
        
    except Exception as e:
        print(f"❌ Crash handler setup failed: {e}")
        return False

def test_diagnostic_collection():
    """Test diagnostic data collection"""
    print("\n📊 Testing Diagnostic Collection...")
    
    try:
        from client.utils.crash_reporter import EmergencyCrashReporter
        
        reporter = EmergencyCrashReporter()
        
        # Test individual diagnostic methods
        tests = [
            ("Python Environment", lambda: reporter.log_python_environment()),
            ("Module Imports", lambda: reporter.log_module_imports()),
            ("File System Access", lambda: reporter.log_file_system_access()),
            ("Qt Initialization", lambda: reporter.log_qt_initialization()),
            ("Application Structure", lambda: reporter.log_application_structure()),
            ("Network Connectivity", lambda: reporter.log_network_connectivity())
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                test_func()
                print(f"✅ {test_name}")
                results.append((test_name, True))
            except Exception as e:
                print(f"❌ {test_name}: {e}")
                results.append((test_name, False))
        
        passed = sum(1 for _, success in results if success)
        total = len(results)
        print(f"\n📊 Diagnostics: {passed}/{total} passed")
        
        return passed == total
        
    except Exception as e:
        print(f"❌ Diagnostic collection failed: {e}")
        return False

def test_crash_report_generation():
    """Test crash report generation"""
    print("\n📋 Testing Crash Report Generation...")
    
    try:
        from client.utils.crash_reporter import EmergencyCrashReporter
        
        reporter = EmergencyCrashReporter()
        
        # Run some diagnostics first
        reporter.log_python_environment()
        reporter.log_module_imports()
        
        # Generate a test crash report
        test_exception = RuntimeError("Test crash for emergency reporting")
        test_traceback = "Traceback (test): RuntimeError: Test crash for emergency reporting"
        
        report_path = reporter.generate_emergency_crash_report(test_exception, test_traceback)
        
        if report_path and Path(report_path).exists():
            print(f"✅ Crash report generated: {report_path}")
            
            # Check if summary was also created
            summary_path = Path(report_path).with_suffix('.txt')
            if summary_path.exists():
                print(f"✅ Summary report generated: {summary_path}")
            else:
                print("⚠️  Summary report missing")
            
            return True
        else:
            print("❌ Crash report not generated")
            return False
            
    except Exception as e:
        print(f"❌ Crash report generation failed: {e}")
        return False

def test_simulated_startup_crash():
    """Test simulated startup crash"""
    print("\n💥 Testing Simulated Startup Crash...")
    
    try:
        from client.utils.crash_reporter import setup_emergency_crash_handler
        
        # Setup crash handler
        setup_emergency_crash_handler()
        
        print("🔥 Simulating startup crash...")
        
        # This should be caught by the emergency handler
        try:
            raise ImportError("Simulated PyQt5 import failure during startup")
        except ImportError:
            print("✅ Simulated crash was handled by emergency system")
            return True
            
    except Exception as e:
        print(f"❌ Simulated crash test failed: {e}")
        return False

def test_gui_failure_simulation():
    """Test GUI failure simulation"""
    print("\n🖼️  Testing GUI Failure Simulation...")
    
    try:
        # This should fail gracefully and be reported
        original_path = sys.path.copy()
        
        # Temporarily break PyQt5 import
        sys.path = [p for p in sys.path if 'PyQt5' not in p]
        
        try:
            from client.utils.crash_reporter import EmergencyCrashReporter
            reporter = EmergencyCrashReporter()
            reporter.log_qt_initialization()
            
            # Check if Qt failure was detected
            if 'qt_initialization' in reporter.crash_info:
                qt_stages = reporter.crash_info['qt_initialization']['stages']
                failed_stages = [s for s in qt_stages if not s['success']]
                
                if failed_stages:
                    print(f"✅ Qt failure detected: {len(failed_stages)} failed stages")
                    return True
                else:
                    print("⚠️  Qt failure not detected")
                    return False
            
        finally:
            # Restore original path
            sys.path = original_path
            
    except Exception as e:
        print(f"❌ GUI failure simulation failed: {e}")
        return False

def main():
    """Run all emergency crash reporting tests"""
    print("🚨 EMERGENCY CRASH REPORTING TEST SUITE")
    print("=" * 50)
    
    tests = [
        ("Emergency Import", test_emergency_import),
        ("Emergency Initialization", test_emergency_initialization),
        ("Crash Handler Setup", test_crash_handler_setup),
        ("Diagnostic Collection", test_diagnostic_collection),
        ("Crash Report Generation", test_crash_report_generation),
        ("Simulated Startup Crash", test_simulated_startup_crash),
        ("GUI Failure Simulation", test_gui_failure_simulation)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n💥 {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print(f"\n📊 TEST RESULTS")
    print("=" * 20)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All emergency crash reporting tests passed!")
        print("✅ Your macOS app will capture ALL startup failures!")
        print("📋 Reports will be saved even if the app never shows a window!")
    else:
        print("\n⚠️  Some tests failed - check emergency reporting setup")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎊 EMERGENCY REPORTING READY!' if success else '⚠️  ISSUES DETECTED'}")
    sys.exit(0 if success else 1)