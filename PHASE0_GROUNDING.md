# Phase 0 Grounding

Date: 2026-07-26

## Local references saved

- `../research/genlayer-api.txt`
- `../research/genlayer-docs.txt`

Both were downloaded from the current GenLayer documentation endpoints required by the brief:

- `https://sdk.genlayer.com/main/_static/ai/api.txt`
- `https://docs.genlayer.com/full-documentation.txt`

## Tooling

- `genlayer.cmd --version`: 0.39.2
- `genvm-lint --version`: 0.11.0
- `gltest --version`: pytest 9.1.1 via `genlayer-test` 0.29.2
- `genlayer.cmd network set studionet`: completed successfully after allowing the CLI to write `C:\Users\DELL\.genlayer\genlayer-config.json`.

PowerShell cannot run the `.ps1` shims under the current execution policy, so Windows `.cmd` wrappers should be used for CLI commands:

```powershell
genlayer.cmd --version
genlayer.cmd network set studionet
```

## API surface checked locally

The required symbols were searched in the downloaded docs before choosing an idea:

- `gl.nondet.web.render`
- `gl.nondet.web.get`
- `gl.nondet.exec_prompt`
- `gl.eq_principle.prompt_comparative`
- `gl.eq_principle.prompt_non_comparative`
- `gl.eq_principle.strict_eq`
- `gl.vm.run_nondet`
- `gl.vm.run_nondet_unsafe`
- `gl.Contract`
- `gl.public.write`
- `gl.public.view`
- `gl.contract_interface`
- `gl.evm.contract_interface`
- `gl.Event`
- `TreeMap`
- `DynArray`
- `allow_storage`
- `Address`
- `Keccak256`
- `emit_transfer`
- `gl.message.value`

Notable exact confirmations from `../research/genlayer-api.txt`:

- `genlayer.vm.run_nondet(leader_fn, validator_fn, **kwargs)`
- `genlayer.vm.run_nondet_unsafe(leader_fn, validator_fn, **kwargs)`
- `genlayer.eq_principle.prompt_comparative(fn, principle)`
- `genlayer.eq_principle.prompt_non_comparative(fn, principle)`
- `genlayer.eq_principle.strict_eq(fn)`
- `emit_transfer(value: u256, *, on: ContractAt.ReceiptType = 'finalized')`
- `genlayer.message.value`

## Ecosystem scan notes

The public ecosystem page states the ecosystem includes 200+ builders, 42 validators, 86K+ creators, 1M+ testnet activity, and 14+ partners. The portal/hackathon page names example areas and projects including:

- `internetcourt.org`
- `mergeproof.com`
- `molly.fun`
- `argue.fun`
- Progressive Autonomy in DAOs
- COFI bets
- P2P bets
- Prediction Market Kit
- Mochi: Saving the Consensus
- Unstoppable
- rally.fun
- Cross border settlement
- Intelligent Oracle
- Polymarket Benchmark

The brief also bans two current-cycle collisions:

- Semantic change-detection on watched web pages
- Multi-source corroboration / independence-clustering oracles with source reputation

The selected idea below avoids page-change monitoring and source-corroboration/reputation oracles.
