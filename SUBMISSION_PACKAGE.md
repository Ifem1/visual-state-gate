# Submission Package Draft

## Title

Visual State Gate

## Notes

Visual State Gate is a GenLayer primitive for contracts that need consensus on what a public webpage visibly shows. Review fix: the public consumer-key index is now caller-namespaced as requester address plus consumer key, so another caller cannot replace what latest_request_for returns for the original requester. The model never decides contract behavior: validation, confidence bands, retry caps, storage writes, and can_pass() are deterministic. Evidence: primitive and consumer lint clean; 29 direct tests pass including namespace regression tests. Patched StudioNet deploy at 0x235B325a7598154Eb65F6948791c023Be8b71D76: deploy and request_check were accepted; resolve attempts hit NO_MAJORITY during StudioNet/RPC pressure and left state unchanged.

## Character Count

The notes paragraph is 755 characters, counted programmatically with PowerShell `.Length`.

## Evidence Links

- GitHub repo: https://github.com/Ifem1/visual-state-gate
- Explorer contract page: https://explorer-studio.genlayer.com/address/0x235B325a7598154Eb65F6948791c023Be8b71D76
- Studio import: network `studionet`, contract address `0x235B325a7598154Eb65F6948791c023Be8b71D76`

## Review Fix

- Issue: public `consumer_key` index could be overwritten by another caller using the same key.
- Fix: latest index is now keyed by `requester_address + ":" + consumer_key`.
- API compatibility: `latest_request_for(consumer_key)` is unchanged; it now reads from the caller namespace.

## Verification

- `pytest tests/direct/ -q`: `29 passed`
- `genvm-lint check contracts\visual_state_gate.py --json`: `ok: true`
- `genvm-lint check examples\visual_gate_consumer.py --json`: `ok: true`

## Patched Deployment

- Contract: `0x235B325a7598154Eb65F6948791c023Be8b71D76`
- Deploy tx: `0xc58a426fd70bc2f68f65023f1481a612b41824549a5b7fd5bddc1a3bc24d7064`
- `request_check` tx: `0x7e5b8d4193099aaa140bc1414fe42512bcb838ccc3ec16ba523e1a57338daf5c`
- `resolve` attempts: `0xe9f41a69947fe7abbad7de5e81fd7f3daf223facc8ba3f934ae8d46a0db8e025`, `0xa3920125a0a76eb2c853fd3153675e850d687e02c6b23c29e343c4498fd5e002`

## Note

Resolve attempts during the patched resubmission window returned `CANCELED / NO_MAJORITY`, then StudioNet rate-limited further retries. The request remained `PENDING`, as expected when no consensus round writes state.
