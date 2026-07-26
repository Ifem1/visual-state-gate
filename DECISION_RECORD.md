# Decision Record: Visual State Gate

## Chosen primitive

`VisualStateGate` is a standalone Intelligent Contract primitive that renders a public URL as a screenshot, asks validator consensus whether the visible state satisfies a caller-supplied semantic condition, and exposes the resulting verdict to downstream contracts through a small interface.

The primitive is for builders who need to gate money, access, membership, or another state transition on what a public page visibly shows, especially when the page has no stable API and a deterministic DOM parser would miss charts, banners, badges, maps, dashboards, modals, rendered receipts, or screenshots-as-content.

## Candidate generation

1. Visual state gate: render a public page screenshot and decide whether a requested UI state is visibly present; imported by escrow, access, and reputation contracts.
2. Screenshot-backed milestone escrow: hold GEN and release it when a public preview page visibly satisfies a milestone; imported by bounty and contracting systems.
3. Visual receipt reimbursement vault: reimburse an agent only when a public receipt or hosted invoice image visibly matches amount, merchant, and date; imported by agent commerce wallets.
4. Bonded claim slashing primitive: require a claimant bond and slash it if consensus judges that their evidence does not support the claim; imported by dispute and reporting systems.
5. Semantic callback router: call one of several downstream contract methods based on a consensus verdict; imported by contracts that need adjudicated branching without embedding nondet logic.
6. Screenshot compliance badge gate: grant access only when a public profile visibly contains a required badge or disclosure; imported by membership contracts.
7. Visual inventory availability gate: judge whether a rendered product page visibly says an item is in stock, discontinued, or waitlisted; imported by agent procurement contracts.
8. Embedding-backed policy matcher: store approved policy clauses in a vector database and route new clauses to the nearest allowed policy family; imported by governance and compliance contracts.
9. Semantic duplicate registry: embed artifact descriptions and reject new registrations that are too semantically close to existing ones; imported by registries and grant programs.
10. EVM transaction explanation gate: read EVM transaction metadata and gate an Intelligent Contract state transition on whether the apparent action matches a declared purpose; imported by cross-chain accountability contracts.
11. Contract factory for adjudication vaults: deploy minimal configured gate contracts for many markets/projects; imported by platforms that need isolated state and immutable settings.
12. Sandboxed rule evaluator: run a caller-supplied deterministic scoring script in a sub-VM after consensus normalizes evidence; imported by systems that need constrained custom rules.

Distinct capability coverage:

- Live web/API access: 1, 2, 6, 7
- Image and visual evidence: 1, 2, 3, 6, 7
- Native value: 2, 3, 4
- Contract-to-contract composition: 5, 11
- Embeddings/vector search: 8, 9
- EVM interop: 10
- Contract factories and sandboxing: 11, 12

The two most similar candidates are `Visual state gate` and `Screenshot compliance badge gate`. They are not separate primitives: the compliance badge version is a use case of the broader visual gate, so it was not chosen independently.

If web access did not exist, the best candidate would be the embedding-backed policy matcher because it still uses GenLayer storage plus semantic comparison as an importable primitive. It was not chosen because the current category brief specifically calls image evidence underused, and visual evidence creates a clearer trust problem than internal-only semantic matching.

The strongest discarded candidate was the bonded claim slashing primitive. It has strong native-value alignment, but without a very precise evidence source it risks becoming a generic dispute app. The visual gate is narrower, easier to reuse, and easier to test adversarially.

## Screening

### Gate A: Counterfactual

Without GenLayer, one backend or one screenshot service would decide whether the visible state satisfied the condition. That breaks the primitive because both the page operator and the downstream beneficiary may have incentives around the outcome. GenLayer keeps the visual observation, semantic judgement, and on-chain gate in the same consensus domain.

### Gate B: Trust problem

The mutually distrusting parties are:

- The party that benefits from the condition being true, such as a contractor, claimant, applicant, or agent.
- The counterparty that pays, admits, routes, or changes state only if the condition is genuinely true.

In some use cases, the claimant may control the page being rendered. In others, the counterparty may choose the requirement text. The contract must constrain both through deterministic validation, bounded prompts, abstention, and immutable request records.

### Gate C: Judgement

The core question is semantic and visual: does the screenshot visibly support the requested condition? This is not equivalent to checking a CSS selector, parsing JSON, or reading one numeric feed. Equivalent answers can use different wording, but cannot change the verdict, confidence band, cited visible evidence, or abstention reason.

### Gate D: Importability

Consumer integration target:

```python
@gl.contract_interface
class IVisualStateGate:
    class View:
        def verdict(self, request_id: str) -> str: ...
    class Write:
        def request_check(self, url: str, condition: str, callback: Address) -> str: ...

gate = IVisualStateGate(self.gate_address)
request_id = gate.emit().request_check(url, condition, self.address)
```

The consumer imports a gate, submits a URL and condition, then reads or receives the verdict. It does not embed screenshot rendering, prompt design, output parsing, or equivalence principles.

### Gate E: Consequential decision

The primitive gates downstream money movement, access, membership, permissions, or contract control flow. The first implementation should include callback and pull-based reads so consumers can decide whether to react immediately or poll after finality.

### Gate F: Originality

The public ecosystem and hackathon examples emphasize arbitration, prediction markets, betting, project/product flows, merge proof, work platforms, and generic intelligent oracles. The brief explicitly bans semantic web-page change detection and multi-source corroboration oracles. `VisualStateGate` is not watching pages over time and is not clustering multiple sources; it is a reusable screenshot-evidence gate for visible state at request time.

## Initial design commitments

Non-determinism budget:

1. `gl.nondet.web.render(url, mode="screenshot")` to produce the visible evidence.
2. `gl.nondet.exec_prompt(prompt, images=[screenshot])` to classify the screenshot against the condition.

Everything else must stay deterministic: request IDs, input validation, caps, cooldowns, thresholds, output parsing, confidence bands, verdict normalization, storage writes, events, callback dispatch, and any consumer-facing method selection.

Equivalence principle:

Validators compare whether the screenshot visibly supports the exact requested condition. Equivalent outputs may phrase evidence differently and may cite visible elements in a different order. They are not equivalent if they change the verdict, confidence band, page identity, requested condition, visible evidence that is material to the verdict, or abstention reason.

Failure semantics:

- Failed rendering is `UNKNOWN`, never `FALSE`.
- Unparseable model output is `UNKNOWN`.
- Missing or ambiguous evidence is `UNKNOWN`.
- Safe failure is no downstream approval and no value movement by this primitive.

Consumer interface:

The primitive should support pull first, with an optional callback. Pull is safer because a consumer can handle finality and retries explicitly. Callback is useful for composition but should not move value on `accepted`.

Trust model:

Request records are immutable once submitted. The requester cannot edit a condition after seeing the screenshot result. The owner, if any, must not be able to overwrite verdicts or lower safety thresholds for existing requests.

## Folder created

This folder is the final-idea workspace:

```text
visual-state-gate/
```
