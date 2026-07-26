# VisualStateGate Design

## Nondeterminism budget

The primitive uses exactly two nondeterministic operations in one consensus round:

1. `gl.nondet.web.render(url, mode="screenshot", wait_after_loaded="1s")`
   - Needed because the page's visible state can depend on browser rendering, client-side JavaScript, images, canvas, CSS, and layout.
   - A deterministic parser would see only source text or API data, not the rendered page a human or downstream protocol cares about.

2. `gl.nondet.exec_prompt(prompt, images=[screenshot])`
   - Needed because the core question is semantic and visual: whether the screenshot visibly supports the requested condition.
   - The model is asked only what the screenshot shows. It is never asked what the contract should do.

No second source fetch, reputation scoring, historical diffing, or off-chain report is used in the first implementation.

## Deterministic surface

The following are deterministic contract code:

- URL, condition, subject, and request-id validation.
- Request immutability after creation.
- Attempt caps.
- Storage writes.
- Verdict normalization into `PASS`, `FAIL`, or `UNKNOWN`.
- Confidence normalization into `HIGH`, `MEDIUM`, `LOW`, or `NONE`.
- Output parsing and safe defaults.
- All view results.
- Whether a downstream consumer may treat a verdict as approved.

Every payout-adjacent or access-adjacent state transition is deterministic code acting on consensus-agreed output. The prompt can say what the visible world supports; it cannot select contract behavior.

## Equivalence principle

For the visual judgement block:

Validators compare whether the leader and validator answers are materially the same judgement about the screenshot and requested condition. Equivalent outputs may phrase the explanation differently, cite visible evidence in a different order, or use different casing for labels that normalize to the same band. They are not equivalent if they change the verdict, confidence band, requested condition, page identity, material visible evidence, or abstention reason. A different number, date, name, status, badge, amount, product state, or UI label is not equivalent when it affects the verdict.

The implementation uses `prompt_comparative`, not `prompt_non_comparative`, because the answer gates downstream contract decisions.

## Failure and abstention

- Render failure is represented as `UNKNOWN`; it is not interpreted as `FAIL`.
- Model output that is not JSON, lacks required keys, invents an invalid label, or exceeds caps is normalized safely.
- Ambiguous, obscured, stale, off-screen, or visually insufficient evidence is `UNKNOWN`.
- `UNKNOWN` never allows the consumer helper `can_pass()` to return true.
- `UNKNOWN` can be retried while attempts remain; `PASS` and `FAIL` are terminal.

Safe failure direction: do not approve. This primitive should never release value or grant access on absence of consensus-backed visible evidence.

## Storage layout

Storage is bounded by constructor parameters:

- `max_requests`
- `max_attempts`
- `max_url_chars`
- `max_condition_chars`
- `max_subject_chars`
- `max_evidence_chars`

Each request is stored in a `TreeMap[str, VisualRequest]`, and request IDs are assigned monotonically from `next_id`. The current implementation does not use unbounded arrays.

## Consumer interface

The primary interface is pull-based:

```python
gate = IVisualStateGate(self.gate)
request_id = gate.view().latest_request_for(self.address_string)
verdict = gate.view().verdict(request_id)
```

Pull is safer for first release because consumers decide how to handle finality, retry, and value movement. The primitive stores a `consumer_key` string so downstream contracts and indexers can find requests without embedding callback machinery.

## Trust model

There is no owner-controlled override. Constructor parameters cap the surface, but they are immutable after deploy. The requester chooses the URL and condition, yet cannot mutate them after request creation. Resolution is permissionless and can be retried only while the status is `PENDING` or `UNKNOWN` and attempts remain.

## Latency budget

Registration is deterministic and should settle quickly. Resolution is the slow path: one rendered screenshot plus one model judgement in a comparative equivalence block. Consumers should call `request_check()` first, then call `resolve()` separately when they are ready to wait for consensus.
