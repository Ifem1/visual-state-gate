from tests.conftest import as_hex_address, deploy_gate


CONF_HIGH = "HIGH"
CONF_NONE = "NONE"
ERROR_EXPECTED = "EXPECTED"
ERROR_LLM = "LLM_ERROR"
STATUS_FAIL = "FAIL"
STATUS_PASS = "PASS"
STATUS_PENDING = "PENDING"
STATUS_UNKNOWN = "UNKNOWN"


def test_request_stores_immutable_pending_record(direct_deploy):
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/status",
        "The page visibly shows the deployment status is Complete.",
        "deployment",
        "consumer-a",
    )

    record = gate.get_request(request_id)
    assert record["exists"] is True
    assert record["url"] == "https://example.com/status"
    assert record["condition"] == "The page visibly shows the deployment status is Complete."
    assert record["subject"] == "deployment"
    assert record["consumer_key"] == "consumer-a"
    assert record["status"] == STATUS_PENDING
    assert gate.latest_request_for("consumer-a") == request_id


def test_request_uses_sender_as_consumer_when_key_is_blank(direct_deploy, direct_owner):
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/status",
        "The page visibly shows the deployment status is Complete.",
    )

    assert gate.latest_request_for(as_hex_address(direct_owner)) == request_id


def test_unknown_request_reads_fail_closed(direct_deploy):
    gate = deploy_gate(direct_deploy)

    assert gate.verdict("missing") == STATUS_UNKNOWN
    assert gate.can_pass("missing") is False
    record = gate.get_request("missing")
    assert record["exists"] is False
    assert record["error_code"] == ERROR_EXPECTED


def test_invalid_url_rejects_http(direct_vm, direct_deploy):
    gate = deploy_gate(direct_deploy)

    with direct_vm.expect_revert("url must be https"):
        gate.request_check("http://example.com", "The page visibly shows an approved badge.")


def test_invalid_url_rejects_missing_domain(direct_vm, direct_deploy):
    gate = deploy_gate(direct_deploy)

    with direct_vm.expect_revert("url must be https"):
        gate.request_check("https://localhost", "The page visibly shows an approved badge.")


def test_empty_condition_reverts(direct_vm, direct_deploy):
    gate = deploy_gate(direct_deploy)

    with direct_vm.expect_revert("condition is required"):
        gate.request_check("https://example.com", "")


def test_overlong_url_reverts_instead_of_truncating(direct_vm, direct_deploy):
    gate = deploy_gate(direct_deploy, max_url_chars=40)

    with direct_vm.expect_revert("url is too long"):
        gate.request_check(
            "https://example.com/" + ("a" * 80),
            "The page visibly shows an approved badge.",
        )


def test_overlong_condition_reverts_instead_of_truncating(direct_vm, direct_deploy):
    gate = deploy_gate(direct_deploy, max_condition_chars=40)

    with direct_vm.expect_revert("condition is too long"):
        gate.request_check("https://example.com", "x" * 80)


def test_request_cap_is_enforced(direct_vm, direct_deploy):
    gate = deploy_gate(direct_deploy, max_requests=1)
    gate.request_check("https://example.com/one", "The page visibly shows an approved badge.")

    with direct_vm.expect_revert("request cap reached"):
        gate.request_check("https://example.com/two", "The page visibly shows an approved badge.")


def test_constructor_rejects_unbounded_request_cap(direct_vm, direct_deploy):
    with direct_vm.expect_revert("max_requests out of range"):
        deploy_gate(direct_deploy, max_requests=10001)


def test_constructor_rejects_zero_attempts(direct_vm, direct_deploy):
    with direct_vm.expect_revert("max_attempts out of range"):
        deploy_gate(direct_deploy, max_attempts=0)


def test_sequential_request_ids_are_monotonic(direct_deploy):
    gate = deploy_gate(direct_deploy)

    first = gate.request_check(
        "https://example.com/one",
        "The page visibly shows an approved badge.",
    )
    second = gate.request_check(
        "https://example.com/two",
        "The page visibly shows an approved badge.",
    )

    assert first == "vsg-1"
    assert second == "vsg-2"


def test_latest_request_for_consumer_updates_to_newest(direct_deploy):
    gate = deploy_gate(direct_deploy)

    first = gate.request_check(
        "https://example.com/one",
        "The page visibly shows an approved badge.",
        "",
        "consumer-a",
    )
    second = gate.request_check(
        "https://example.com/two",
        "The page visibly shows an approved badge.",
        "",
        "consumer-a",
    )

    assert first == "vsg-1"
    assert gate.latest_request_for("consumer-a") == second


def test_latest_request_for_is_namespaced_by_sender(direct_vm, direct_deploy, direct_bob):
    gate = deploy_gate(direct_deploy)

    owner_request = gate.request_check(
        "https://example.com/owner",
        "The page visibly shows an approved badge.",
        "",
        "shared-key",
    )
    with direct_vm.prank(direct_bob):
        bob_request = gate.request_check(
            "https://example.com/bob",
            "The page visibly shows an approved badge.",
            "",
            "shared-key",
        )
        assert gate.latest_request_for("shared-key") == bob_request

    assert gate.latest_request_for("shared-key") == owner_request


def test_blank_consumer_key_latest_is_namespaced_by_sender(
    direct_vm, direct_deploy, direct_owner, direct_bob
):
    gate = deploy_gate(direct_deploy)

    owner_request = gate.request_check(
        "https://example.com/owner",
        "The page visibly shows an approved badge.",
    )
    with direct_vm.prank(direct_bob):
        bob_request = gate.request_check(
            "https://example.com/bob",
            "The page visibly shows an approved badge.",
        )
        assert gate.latest_request_for("") == bob_request

    assert gate.latest_request_for("") == owner_request
    assert gate.latest_request_for(as_hex_address(direct_owner)) == owner_request


def test_latest_request_for_unknown_consumer_is_blank(direct_deploy):
    gate = deploy_gate(direct_deploy)

    assert gate.latest_request_for("nobody") == ""


def test_pending_request_never_passes_consumer_gate(direct_deploy):
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/one",
        "The page visibly shows an approved badge.",
    )

    assert gate.verdict(request_id) == STATUS_PENDING
    assert gate.can_pass(request_id) is False


def test_config_reports_bounded_storage_parameters(direct_deploy):
    gate = deploy_gate(
        direct_deploy,
        max_requests=7,
        max_attempts=2,
        max_url_chars=120,
        max_condition_chars=140,
        max_subject_chars=60,
        max_evidence_chars=100,
    )

    config = gate.get_config()
    assert config["max_requests"] == 7
    assert config["max_attempts"] == 2
    assert config["next_id"] == 1


def test_requester_is_captured_from_sender(direct_vm, direct_deploy, direct_bob):
    gate = deploy_gate(direct_deploy)

    with direct_vm.prank(direct_bob):
        request_id = gate.request_check(
            "https://example.com/member",
            "The page visibly shows an approved badge.",
        )

    assert gate.get_request(request_id)["requester"] == as_hex_address(direct_bob)


def test_render_failure_records_unknown_external_not_fail_or_pass(direct_vm, direct_deploy):
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "screenshot"})
    direct_vm.mock_llm(
        r"deployment status is Complete",
        '{"verdict":"PASS","confidence":"HIGH","evidence":"The screenshot visibly shows Complete.","error_code":"NONE"}',
    )
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/status",
        "The page visibly shows the deployment status is Complete.",
    )

    gate.resolve(request_id)

    record = gate.get_request(request_id)
    assert record["status"] == STATUS_UNKNOWN
    assert record["error_code"] == "EXTERNAL"
    assert gate.can_pass(request_id) is False


def test_resolve_fails_closed_on_low_confidence_pass(direct_vm, direct_deploy):
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "screenshot"})
    direct_vm.mock_llm(
        r"approved badge",
        '{"verdict":"PASS","confidence":"LOW","evidence":"Maybe a badge","error_code":"NONE"}',
    )
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/member",
        "The page visibly shows an approved badge.",
    )

    gate.resolve(request_id)

    assert gate.verdict(request_id) == STATUS_UNKNOWN
    assert gate.can_pass(request_id) is False


def test_resolve_unknown_can_be_retried_until_attempt_cap(direct_vm, direct_deploy):
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "screenshot"})
    direct_vm.mock_llm(
        r"approved badge",
        '{"verdict":"UNKNOWN","confidence":"NONE","evidence":"","error_code":"EXPECTED"}',
    )
    gate = deploy_gate(direct_deploy, max_attempts=2)
    request_id = gate.request_check(
        "https://example.com/member",
        "The page visibly shows an approved badge.",
    )

    gate.resolve(request_id)
    gate.resolve(request_id)

    record = gate.get_request(request_id)
    assert record["status"] == STATUS_UNKNOWN
    assert record["attempts"] == 2
    with direct_vm.expect_revert("attempt cap reached"):
        gate.resolve(request_id)


def test_external_unknown_is_retryable_not_terminal(direct_vm, direct_deploy):
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "screenshot"})
    direct_vm.mock_llm(
        r"approved badge",
        '{"verdict":"PASS","confidence":"HIGH","evidence":"Badge visible","error_code":"NONE"}',
    )
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/member",
        "The page visibly shows an approved badge.",
    )
    gate.resolve(request_id)

    assert gate.verdict(request_id) == STATUS_UNKNOWN
    gate.resolve(request_id)
    assert gate.get_request(request_id)["attempts"] == 2


def test_external_unknown_stops_at_attempt_cap(direct_vm, direct_deploy):
    direct_vm.mock_web(r"example\.com", {"status": 200, "body": "screenshot"})
    direct_vm.mock_llm(
        r"approved badge",
        '{"verdict":"FAIL","confidence":"HIGH","evidence":"No badge visible","error_code":"NONE"}',
    )
    gate = deploy_gate(direct_deploy, max_attempts=1)
    request_id = gate.request_check(
        "https://example.com/member",
        "The page visibly shows an approved badge.",
    )
    gate.resolve(request_id)

    with direct_vm.expect_revert("attempt cap reached"):
        gate.resolve(request_id)


def test_resolve_unknown_request_reverts(direct_vm, direct_deploy):
    gate = deploy_gate(direct_deploy)

    with direct_vm.expect_revert("unknown request"):
        gate.resolve("vsg-missing")


def test_subject_hint_is_cleaned_before_storage(direct_deploy):
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/member",
        "The page visibly shows an approved badge.",
        " badge\x00\n  row ",
    )

    assert gate.get_request(request_id)["subject"] == "badge row"


def test_consumer_key_is_cleaned_before_indexing(direct_deploy):
    gate = deploy_gate(direct_deploy)
    request_id = gate.request_check(
        "https://example.com/member",
        "The page visibly shows an approved badge.",
        "",
        " team\x00\n  alpha ",
    )

    assert gate.latest_request_for("team alpha") == request_id


def test_evidence_cap_is_reported_in_config(direct_deploy):
    gate = deploy_gate(direct_deploy, max_evidence_chars=120)

    assert gate.get_config()["max_evidence_chars"] == 120


def test_request_cap_boundary_allows_exact_limit(direct_deploy):
    gate = deploy_gate(direct_deploy, max_requests=2)

    first = gate.request_check(
        "https://example.com/one",
        "The page visibly shows an approved badge.",
    )
    second = gate.request_check(
        "https://example.com/two",
        "The page visibly shows an approved badge.",
    )

    assert first == "vsg-1"
    assert second == "vsg-2"
