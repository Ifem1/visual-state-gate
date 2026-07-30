# Visual State Gate

Visual State Gate is a standalone GenLayer Intelligent Contract primitive for contracts that need consensus on what a public webpage visibly shows.

It is not a frontend, app, or recommendation engine. A consumer contract submits a URL and a precise visual condition, anyone resolves it through a screenshot-based consensus round, and downstream logic reads `PASS`, `FAIL`, or `UNKNOWN`.

## Why This Exists

Many consequential states are visible but not cleanly machine-readable: a dashboard says a deployment is complete, a public profile displays a required badge, a hosted receipt shows a merchant and amount, or a product page renders a waitlist label through client-side JavaScript.

A backend screenshot service would make one operator the judge. A DOM parser misses canvas, images, layout, hidden overlays, and rendered UI. A single LLM call produces an off-chain opinion. Visual State Gate keeps the rendered evidence, semantic judgement, and contract-readable result in one consensus domain.

## How It Works

1. A caller submits `request_check(url, condition, subject, consumer_key)`.
2. The contract validates the URL and text, stores an immutable pending request, and indexes it under the caller namespace.
3. Anyone calls `resolve(request_id)`.
4. Validators render a screenshot with `gl.nondet.web.render`.
5. Validators compare the visual judgement with `gl.eq_principle.prompt_comparative`.
6. The contract deterministically normalizes `PASS`, `FAIL`, or `UNKNOWN`.
7. Consumers read `verdict`, `can_pass`, `get_request`, or `latest_request_for`.

## Review Fix: Consumer-Key Namespacing

Joaquin flagged that the original public consumer-key index was not protected: any caller could reuse another caller's `consumer_key` and replace what `latest_request_for` returned.

This is fixed in the patched contract. Internally the latest index key is:

```text
requester_address + ":" + consumer_key
```

`latest_request_for(consumer_key)` now looks up the caller's own namespace. Another caller may reuse the same public key text, but they only update their own namespace. Blank keys are also caller-namespaced by sender address.

The public API shape is unchanged.

## Consensus Boundary

Nondeterministic operations:

- `gl.nondet.web.render(url, mode="screenshot", wait_after_loaded="1s")`
- `gl.nondet.exec_prompt(prompt, images=[screenshot])`

Everything else is deterministic: request IDs, validation, caps, consumer-key namespacing, verdict labels, confidence labels, storage writes, retry rules, and consumer-facing approval.

Equivalence principle:

> Compare the leader and validator outputs as visual evidence judgements for a GenLayer contract. The answer is equivalent only when it preserves the same verdict, confidence band, requested condition, page identity, material visible evidence, and abstention reason. Wording, ordering of evidence bullets, casing, and minor style differences are equivalent when they do not change meaning. A different visible amount, date, name, status, badge, product state, UI label, or any different PASS/FAIL/UNKNOWN result is not equivalent. UNKNOWN is equivalent only to UNKNOWN for substantially the same abstention reason, such as unreadable page, ambiguous evidence, inaccessible render, or insufficient visual support.

## API

Writes:

- `request_check(url, condition, subject="", consumer_key="") -> str`
- `resolve(request_id) -> None`

Views:

- `verdict(request_id) -> str`
- `can_pass(request_id) -> bool`
- `latest_request_for(consumer_key) -> str`
- `get_request(request_id) -> dict`
- `get_config() -> dict`

## Consumer Example

See [examples/visual_gate_consumer.py](</C:/Users/DELL/Downloads/intelligent contracts/visual-state-gate/examples/visual_gate_consumer.py>).

The consumer contains no screenshot rendering, prompt construction, output parsing, or equivalence-principle logic. It only requests a check and later reads `can_pass()`.

## Verification

Local:

```powershell
pytest tests/direct/ -q
genvm-lint check contracts\visual_state_gate.py --json
genvm-lint check examples\visual_gate_consumer.py --json
```

Latest local result:

- `29 passed`
- primitive lint: `ok: true`
- consumer lint: `ok: true`

New regression tests:

- `test_latest_request_for_is_namespaced_by_sender`
- `test_blank_consumer_key_latest_is_namespaced_by_sender`

## Patched StudioNet Deployment

- Contract address: `0x235B325a7598154Eb65F6948791c023Be8b71D76`
- Explorer: https://explorer-studio.genlayer.com/address/0x235B325a7598154Eb65F6948791c023Be8b71D76
- Deployer: `0xa24Ddf60F3a76Ce6f3d491B657b7965Ff8cc6375`
- Deploy tx: `0xc58a426fd70bc2f68f65023f1481a612b41824549a5b7fd5bddc1a3bc24d7064`
- `request_check` tx: `0x7e5b8d4193099aaa140bc1414fe42512bcb838ccc3ec16ba523e1a57338daf5c`
- `resolve` attempts: `0xe9f41a69947fe7abbad7de5e81fd7f3daf223facc8ba3f934ae8d46a0db8e025`, `0xa3920125a0a76eb2c853fd3153675e850d687e02c6b23c29e343c4498fd5e002`

Live patched request:

```text
request_id: vsg-1
url: https://example.com
condition: The page visibly shows the Example Domain heading.
requester: 0xa24Ddf60F3a76Ce6f3d491B657b7965Ff8cc6375
status after request: PENDING
get_config().next_id: 2
```

StudioNet resolve attempts during this resubmission window returned `CANCELED / NO_MAJORITY`, then the RPC rate-limited further retries. Those attempts left state unchanged, which is expected for a non-settled consensus round. This is reported as StudioNet consensus/RPC flakiness, not as a successful visual `PASS`.

## Honest Limits

The direct suite proves the validation, retry, output normalization, fail-closed behavior, and the consumer-key namespace fix. Live visual `PASS` convergence on the patched deployment was not observed during the resubmission window because StudioNet returned `NO_MAJORITY` and then rate-limited. The prior pre-review deployment had shown a live `PASS`, but the canonical submission address is now the patched deployment above.

## Status

- Phase 0 grounding: complete
- Phase 1 decision record: complete
- Phase 2 design: complete
- Primitive contract: implemented
- Worked consumer example: implemented
- Lint: clean
- Direct tests: 29 passed
- Patched StudioNet deployment: complete
- Public GitHub repo: https://github.com/Ifem1/visual-state-gate
