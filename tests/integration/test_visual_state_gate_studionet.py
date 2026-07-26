"""
Full-surface StudioNet integration coverage for VisualStateGate.

Every write method and every view method is exercised against a live
consensus deployment, per the "call every write, read every view" gate.
Resolution rounds are slow (screenshot render + one nondet round) and
StudioNet is known to occasionally return CANCELED/NO_MAJORITY or
UNDETERMINED with nothing written; resolve_until_settled re-submits the
transaction itself when that happens, it does not paper over a contract bug.
"""

from gltest.assertions import tx_execution_failed

from .conftest import resolve_until_settled

EXAMPLE_URL = "https://example.com"
EXAMPLE_CONDITION = "The page visibly shows the Example Domain heading."
TERMINAL_STATUSES = {"PASS", "FAIL", "UNKNOWN"}


def test_get_config_reads_deployed_constructor_values(gate):
    config = gate.get_config(args=[]).call()
    assert config["max_requests"] == 1000
    assert config["max_attempts"] == 3
    assert config["max_url_chars"] == 320
    assert config["max_condition_chars"] == 600
    assert config["max_subject_chars"] == 160
    assert config["max_evidence_chars"] == 500
    assert config["next_id"] == 1


def test_request_check_reverts_on_non_https_url(gate):
    receipt = gate.request_check(
        args=["http://example.com", EXAMPLE_CONDITION, "", "reject-http"]
    ).transact()
    assert tx_execution_failed(receipt)


def test_request_check_reverts_on_empty_condition(gate):
    receipt = gate.request_check(
        args=[EXAMPLE_URL, "", "", "reject-empty-condition"]
    ).transact()
    assert tx_execution_failed(receipt)


def test_resolve_reverts_on_unknown_request_id(gate):
    receipt = gate.resolve(args=["vsg-does-not-exist"]).transact()
    assert tx_execution_failed(receipt)


def test_full_lifecycle_writes_and_reads(gate):
    consumer_key = "studionet-lifecycle"

    write_receipt = gate.request_check(
        args=[EXAMPLE_URL, EXAMPLE_CONDITION, "example.com landing page", consumer_key]
    ).transact()
    assert not tx_execution_failed(write_receipt)

    request_id = gate.latest_request_for(args=[consumer_key]).call()
    assert request_id.startswith("vsg-")

    assert gate.verdict(args=[request_id]).call() == "PENDING"
    assert gate.can_pass(args=[request_id]).call() is False

    pending = gate.get_request(args=[request_id]).call()
    assert pending["exists"] is True
    assert pending["status"] == "PENDING"
    assert pending["attempts"] == 0
    assert pending["consumer_key"] == consumer_key
    assert pending["url"] == EXAMPLE_URL

    config_before = gate.get_config(args=[]).call()

    resolve_receipt = resolve_until_settled(gate, request_id)
    assert not tx_execution_failed(
        resolve_receipt
    ), "resolve did not settle within the network retry budget"

    resolved = gate.get_request(args=[request_id]).call()
    assert resolved["status"] in TERMINAL_STATUSES
    assert resolved["attempts"] >= 1

    verdict = gate.verdict(args=[request_id]).call()
    assert verdict == resolved["status"]

    can_pass = gate.can_pass(args=[request_id]).call()
    if resolved["status"] == "PASS":
        assert resolved["confidence"] == "HIGH"
        assert can_pass is True
    else:
        assert can_pass is False

    if resolved["status"] == "UNKNOWN":
        assert resolved["error_code"] in {"EXTERNAL", "LLM_ERROR", "EXPECTED"}
    else:
        assert resolved["error_code"] == "NONE"

    config_after = gate.get_config(args=[]).call()
    assert config_after["next_id"] == config_before["next_id"]

    if resolved["status"] in {"PASS", "FAIL"}:
        replay_receipt = gate.resolve(args=[request_id]).transact()
        assert tx_execution_failed(
            replay_receipt
        ), "a terminal request must refuse re-resolution"


def test_resolve_convergence_on_identical_url_and_condition(gate):
    consumer_a = "studionet-convergence-a"
    consumer_b = "studionet-convergence-b"

    receipt_a = gate.request_check(
        args=[EXAMPLE_URL, EXAMPLE_CONDITION, "", consumer_a]
    ).transact()
    assert not tx_execution_failed(receipt_a)
    receipt_b = gate.request_check(
        args=[EXAMPLE_URL, EXAMPLE_CONDITION, "", consumer_b]
    ).transact()
    assert not tx_execution_failed(receipt_b)

    request_a = gate.latest_request_for(args=[consumer_a]).call()
    request_b = gate.latest_request_for(args=[consumer_b]).call()
    assert request_a != request_b

    resolve_a = resolve_until_settled(gate, request_a)
    assert not tx_execution_failed(resolve_a)
    resolve_b = resolve_until_settled(gate, request_b)
    assert not tx_execution_failed(resolve_b)

    result_a = gate.get_request(args=[request_a]).call()
    result_b = gate.get_request(args=[request_b]).call()

    assert result_a["status"] == result_b["status"], (
        "two independent consensus rounds over the same URL and condition "
        "must converge on the same verdict category, not merely avoid crashing"
    )
    assert result_a["confidence"] == result_b["confidence"]
