#!/usr/bin/env python3
"""
Test Log Directory Placement
Verify that logs are saved next to the app bundle
"""

import sys
import os
from pathlib import Path

# Add source to path
bundle_source = Path(__file__).parent / "ImgApp_macOS_Bundle" / "source"
sys.path.insert(0, str(bundle_source))

def test_emergency_log_location():
    """Test emergency reporter log location"""
    print("🧪 Testing Emergency Reporter Log Location...")
    
    try:
        from client.utils.crash_reporter import EmergencyCrashReporter
        
        reporter = EmergencyCrashReporter(force_init=False)  # Don't force logging setup
        log_dir = reporter._get_emergency_log_dir()
        
        print(f"📁 Log directory: {log_dir}")
        print(f"📍 Relative to script: {log_dir.relative_to(Path.cwd()) if log_dir.is_relative_to(Path.cwd()) else 'Outside current directory'}")
        
        # Test that it's writable
        try:
            test_file = log_dir / "test_write.tmp"
            test_file.write_text("test", encoding='utf-8')
            test_file.unlink()
            print("✅ Directory is writable")
            writable = True
        except Exception as e:
            print(f"❌ Directory not writable: {e}")
            writable = False
        
        # Check if it's next to the bundle
        bundle_dir = Path(__file__).parent / "ImgApp_macOS_Bundle"
        expected_dir = bundle_dir / "ImgApp_Logs"
        
        if log_dir == expected_dir:
            print("✅ Log directory is next to bundle (as expected)")
            next_to_bundle = True
        else:
            print(f"⚠️  Log directory not next to bundle")
            print(f"   Expected: {expected_dir}")
            print(f"   Actual: {log_dir}")
            next_to_bundle = False
        
        return writable and next_to_bundle
        
    except Exception as e:
        print(f"❌ Emergency log location test failed: {e}")
        return False

def test_regular_log_location():
    """Test regular error reporter log location"""
    print("\n📋 Testing Regular Error Reporter Log Location...")
    
    try:
        from macos_error_reporter import MacOSErrorReporter
        
        reporter = MacOSErrorReporter()
        log_dir = reporter.log_dir
        
        print(f"📁 Log directory: {log_dir}")
        print(f"📍 Relative to script: {log_dir.relative_to(Path.cwd()) if log_dir.is_relative_to(Path.cwd()) else 'Outside current directory'}")
        
        # Check if it's next to the bundle
        bundle_dir = Path(__file__).parent / "ImgApp_macOS_Bundle"
        expected_dir = bundle_dir / "ImgApp_Logs"
        
        if log_dir == expected_dir:
            print("✅ Log directory is next to bundle (as expected)")
            next_to_bundle = True
        else:
            print(f"⚠️  Log directory not next to bundle")
            print(f"   Expected: {expected_dir}")
            print(f"   Actual: {log_dir}")
            next_to_bundle = False
        
        return next_to_bundle
        
    except Exception as e:
        print(f"❌ Regular log location test failed: {e}")
        return False

def test_production_simulation():
    """Simulate production environment (frozen=True)"""
    print("\n🎯 Simulating Production Environment...")
    
    try:
        # Temporarily set frozen state
        original_frozen = getattr(sys, 'frozen', False)
        original_executable = getattr(sys, 'executable', '')
        
        # Simulate macOS .app bundle structure
        fake_app_path = Path.cwd() / "test_app" / "ImgApp.app" / "Contents" / "MacOS" / "ImgApp"
        
        sys.frozen = True
        sys.executable = str(fake_app_path)
        
        try:
            from client.utils.crash_reporter import EmergencyCrashReporter
            
            # Create a fresh instance to test the new logic
            reporter = EmergencyCrashReporter.__new__(EmergencyCrashReporter)
            log_dir = reporter._get_emergency_log_dir()
            
            expected_dir = fake_app_path.parent.parent.parent.parent / "ImgApp_Logs"  # Next to the .app bundle
            
            print(f"📁 Simulated app path: {fake_app_path}")
            print(f"📁 Expected log dir: {expected_dir}")
            print(f"📁 Actual log dir: {log_dir}")
            
            if str(log_dir) == str(expected_dir):
                print("✅ Production log location correct")
                return True
            else:
                print("❌ Production log location incorrect")
                return False
                
        finally:
            # Restore original state
            if original_frozen:
                sys.frozen = original_frozen
            else:
                delattr(sys, 'frozen')
            sys.executable = original_executable
            
    except Exception as e:
        print(f"❌ Production simulation failed: {e}")
        return False

def test_crash_report_with_new_location():
    """Test crash report generation with new location"""
    print("\n💥 Testing Crash Report with New Location...")
    
    try:
        from client.utils.crash_reporter import EmergencyCrashReporter
        
        reporter = EmergencyCrashReporter()
        
        # Generate a test crash report
        test_exception = RuntimeError("Test crash for location verification")
        report_path = reporter.generate_emergency_crash_report(test_exception, "Test traceback")
        
        if report_path and Path(report_path).exists():
            report_file = Path(report_path)
            log_dir = report_file.parent
            
            print(f"📋 Report generated: {report_file.name}")
            print(f"📁 Report location: {log_dir}")
            
            # Check if summary exists
            summary_file = report_file.with_suffix('.txt')
            if summary_file.exists():
                print(f"📄 Summary generated: {summary_file.name}")
            
            # Check if it's in the expected location
            bundle_dir = Path(__file__).parent / "ImgApp_macOS_Bundle"
            expected_dir = bundle_dir / "ImgApp_Logs"
            
            if log_dir == expected_dir:
                print("✅ Report saved next to bundle")
                return True
            else:
                print(f"⚠️  Report not in expected location")
                return False
        else:
            print("❌ Report not generated")
            return False
            
    except Exception as e:
        print(f"❌ Crash report location test failed: {e}")
        return False

def main():
    """Test all log location scenarios"""
    print("📍 LOG LOCATION TEST SUITE")
    print("=" * 30)
    print("Testing that logs are saved next to the app bundle")
    
    tests = [
        ("Emergency Log Location", test_emergency_log_location),
        ("Regular Log Location", test_regular_log_location),
        ("Production Simulation", test_production_simulation),
        ("Crash Report Location", test_crash_report_with_new_location)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n💥 {test_name} crashed: {e}")
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
    
    # Show expected final structure
    print(f"\n📁 EXPECTED STRUCTURE:")
    print(f"ImgApp.app/")
    print(f"├── Contents/")
    print(f"│   └── MacOS/")
    print(f"│       └── ImgApp")
    print(f"└── ImgApp_Logs/          ← Crash reports here!")
    print(f"    ├── emergency_startup_*.log")
    print(f"    ├── EMERGENCY_CRASH_REPORT_*.json")
    print(f"    └── EMERGENCY_CRASH_REPORT_*.txt")
    
    if passed == total:
        print("\n🎉 All log location tests passed!")
        print("✅ Logs will be saved next to the .app bundle!")
        print("👥 Users can easily find crash reports next to the app!")
    else:
        print("\n⚠️  Some tests failed - check log location logic")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)