"""Simple test runner so CI/devs can run tests without pytest installed.

This script will import the pytest-style tests in tests/test_tools_verification.py and run them,
reporting failures and exits with non-zero status if any assertions fail.
"""
import sys
import os
import traceback
import types

# Provide a tiny shim for pytest.skip when running without pytest
class SkipTest(Exception):
    pass

pytest_shim = types.SimpleNamespace()
def _skip(msg=None):
    raise SkipTest(msg)
pytest_shim.skip = _skip

import sys
sys.modules.setdefault('pytest', pytest_shim)

# Ensure repository root and tests directory are on sys.path so imports in tests
# (e.g., `from core import conversion_engine`) resolve when running this script
# from the project root or CI working directory.
HERE = os.path.abspath(os.path.dirname(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, '..'))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from test_tools_verification import (
    test_verify_bundled_tools_returns_expected_structure,
    test_sha256_length_if_present,
    test_checksum_mismatch_detection,
)

failed = 0

for fn in [
    test_verify_bundled_tools_returns_expected_structure,
    test_sha256_length_if_present,
    test_checksum_mismatch_detection,
]:
    try:
        print(f"Running {fn.__name__}...")
        fn()
        print("  OK\n")
    except AssertionError as e:
        print(f"  FAIL: {e}")
        traceback.print_exc()
        failed += 1
    except Exception as e:
        print(f"  ERROR: {e}")
        traceback.print_exc()
        failed += 1

if failed:
    print(f"{failed} tests failed")
    sys.exit(1)
else:
    print("All tests ok")
    sys.exit(0)
