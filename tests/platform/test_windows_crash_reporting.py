#!/usr/bin/env python3
"""
Test Windows Crash Reporting System
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_crash_reporting():
    """Test the crash reporting system"""
    
    print("🧪 Testing Windows Crash Reporting System")
    print("=" * 40)
    
    try:
        from client.utils.crash_reporter import EmergencyCrashReporter
        from client.utils.error_reporter import WindowsErrorReporter, log_info, log_error
        
        print("✅ Crash reporting modules imported successfully")
        
        # Test emergency reporter
        print("\n1. Testing Emergency Crash Reporter...")
        emergency_reporter = EmergencyCrashReporter()
        print(f"✅ Emergency reporter initialized")
        print(f"📁 Log directory: {emergency_reporter.log_dir}")
        
        # Run diagnostics
        print("\n2. Running diagnostics...")
        emergency_reporter.check_python_environment()
        emergency_reporter.check_file_system()
        emergency_reporter.check_gui_dependencies()
        print("✅ All diagnostics completed")
        
        # Test regular error reporter
        print("\n3. Testing Windows Error Reporter...")
        error_reporter = WindowsErrorReporter()
        print(f"✅ Windows error reporter initialized")
        print(f"📁 Log directory: {error_reporter.log_dir}")
        
        # Test logging functions
        print("\n4. Testing logging functions...")
        log_info("This is a test info message", "testing")
        log_error(Exception("Test error for demonstration"), "testing")
        print("✅ Logging functions work")
        
        # Create diagnostic report
        print("\n5. Creating diagnostic report...")
        diag_file = error_reporter.create_diagnostic_report()
        if diag_file:
            print(f"✅ Diagnostic report created: {diag_file}")
        
        # Test emergency crash report (simulated)
        print("\n6. Testing emergency crash report...")
        try:
            raise RuntimeError("Test crash for demonstration")
        except Exception as e:
            json_file, txt_file = emergency_reporter.report_crash(e, "testing")
            print(f"✅ Crash reports created:")
            print(f"  📄 JSON: {json_file}")
            print(f"  📋 TXT: {txt_file}")
        
        print(f"\n🎉 CRASH REPORTING TEST COMPLETE!")
        print(f"📁 All logs saved to: {emergency_reporter.log_dir}")
        
        # Show recent logs
        print(f"\n📋 Recent log files:")
        recent_logs = error_reporter.get_recent_logs(5)
        for log in recent_logs:
            print(f"  • {log['name']} ({log['size']} bytes)")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_crash_reporting()
    sys.exit(0 if success else 1)