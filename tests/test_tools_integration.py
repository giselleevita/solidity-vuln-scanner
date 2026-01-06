from tools_integration import run_slither, run_mythril


def test_slither_runs_or_skips():
    ok, out = run_slither("pragma solidity ^0.8.0; contract X {}", "X.sol")
    # Either it ran or we explain why not
    assert ok in {True, False}
    assert isinstance(out, str)
    # If not installed, message should mention it
    if not ok:
        assert "slither" in out.lower()


def test_mythril_runs_or_skips():
    ok, out = run_mythril("pragma solidity ^0.8.0; contract X {}", "X.sol")
    assert ok in {True, False}
    assert isinstance(out, str)
    if not ok:
        assert "myth" in out.lower() or "mythril" in out.lower()

