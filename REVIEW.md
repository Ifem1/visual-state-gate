# Review Response: Consumer-Key Namespace Protection

## Review Request

Joaquin requested a correction for this issue:

> The public consumer-key index is not protected: any caller can reuse another consumer's key and replace what `latest_request_for` returns. Please bind that index to the caller address or enforce an authorized namespace.

## Fix Summary

The patched contract binds the latest-request index to the caller address.

Before the fix:

- `latest_by_consumer` used only the cleaned `consumer_key`.
- If Alice used `consumer_key = "project-a"`, Bob could submit another request with the same key.
- `latest_request_for("project-a")` would then point at Bob's request.

After the fix:

- The stored index key is `requester_address + ":" + consumer_key`.
- `latest_request_for(consumer_key)` looks up the caller's own namespace.
- Blank consumer keys are also namespaced by caller address.
- The public API shape is unchanged.

## Code Changes

Changed in `contracts/visual_state_gate.py`:

- Added `_namespace_key(owner, consumer_key)`.
- `request_check` now stores latest pointers under the requester namespace.
- `latest_request_for` now reads from the caller namespace instead of the global key.

## Regression Tests

Added direct tests:

- `test_latest_request_for_is_namespaced_by_sender`
- `test_blank_consumer_key_latest_is_namespaced_by_sender`

Current local verification:

- `pytest tests/direct/ -q`: `29 passed`
- `genvm-lint check contracts/visual_state_gate.py --json`: `ok: true`
- `genvm-lint check examples/visual_gate_consumer.py --json`: `ok: true`

## Patched Deployment

Patched StudioNet contract:

`0x235B325a7598154Eb65F6948791c023Be8b71D76`

Explorer:

https://explorer-studio.genlayer.com/address/0x235B325a7598154Eb65F6948791c023Be8b71D76

Live transaction evidence:

- Deploy: `0xc58a426fd70bc2f68f65023f1481a612b41824549a5b7fd5bddc1a3bc24d7064`
- `request_check`: `0x7e5b8d4193099aaa140bc1414fe42512bcb838ccc3ec16ba523e1a57338daf5c`
- `resolve` attempts: `0xe9f41a69947fe7abbad7de5e81fd7f3daf223facc8ba3f934ae8d46a0db8e025`, `0xa3920125a0a76eb2c853fd3153675e850d687e02c6b23c29e343c4498fd5e002`

## Note On StudioNet Resolve

The patched source was deployed and `request_check` was accepted on StudioNet. Resolve attempts during the resubmission window returned `CANCELED / NO_MAJORITY` and left the request `PENDING`, then the RPC rate-limited further retries. This is reported as StudioNet consensus/RPC flakiness, not as a successful visual PASS.
