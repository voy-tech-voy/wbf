import os
import json
import shutil
import pytest

from core import conversion_engine


def test_verify_bundled_tools_returns_expected_structure():
    results = conversion_engine.verify_bundled_tools(timeout=1)
    assert isinstance(results, dict)
    for tool in ['ffmpeg', 'gifsicle']:
        assert tool in results
        entry = results[tool]
        assert 'path' in entry
        assert 'returncode' in entry
        assert 'stdout' in entry
        assert 'stderr' in entry
        # checksum fields should be present (may be None or missing expected value)
        assert 'sha256' in entry or 'expected_sha256' in entry or 'checksum_match' in entry


def test_sha256_length_if_present():
    results = conversion_engine.verify_bundled_tools(timeout=1)
    for tool in ['ffmpeg', 'gifsicle']:
        entry = results.get(tool, {})
        sha = entry.get('sha256')
        if sha is not None:
            assert isinstance(sha, str)
            assert len(sha) == 64


def test_checksum_mismatch_detection(tmp_path=None):
    # If there is a cache directory, write a fake checksums.json and verify checksum_match reports False
    cache = conversion_engine._USER_BIN_CACHE
    if not cache or not os.path.isdir(cache):
        # in pytest this will skip the test, when running via run_tests_no_pytest the pytest shim raises SkipTest
        pytest.skip('No user bin cache available for checksum override test')

    checks_file = os.path.join(cache, 'checksums.json')
    backup = None
    if os.path.exists(checks_file):
        if tmp_path is None:
            import tempfile
            tmp_dir = tempfile.mkdtemp()
            backup = os.path.join(tmp_dir, 'checksums_backup.json')
        else:
            backup = tmp_path / 'checksums_backup.json'
        import shutil
        shutil.copy2(checks_file, str(backup))

    # Build a fake mapping of expected checksums (wrong values)
    fake = {}
    for tool in ['ffmpeg', 'gifsicle']:
        path = conversion_engine.get_bundled_tool_path(tool)
        name = os.path.basename(path)
        fake[name] = '00' * 32  # invalid checksum

    with open(checks_file, 'w', encoding='utf-8') as fh:
        json.dump(fake, fh)

    try:
        results = conversion_engine.verify_bundled_tools(timeout=1)
        for tool in ['ffmpeg', 'gifsicle']:
            entry = results.get(tool, {})
            # If the tool exists, we should have expected_sha256 and checksum_match False
            if entry.get('path') and os.path.exists(entry.get('path')):
                assert entry.get('expected_sha256') == fake.get(os.path.basename(entry.get('path')))
                # checksum_match should be False due to mismatch
                assert entry.get('checksum_match') is False
    finally:
        # restore backup
        if backup and os.path.exists(str(backup)):
            import shutil
            shutil.copy2(str(backup), checks_file)
        else:
            try:
                os.remove(checks_file)
            except Exception:
                pass
