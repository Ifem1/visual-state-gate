# Submission Package Draft

## Title

Visual State Gate

## Notes

Visual State Gate is a GenLayer primitive for contracts that need consensus on what a public webpage visibly shows. It renders a URL as a screenshot, asks comparative validator consensus whether the visible state satisfies a caller-supplied condition, then stores PASS, FAIL, or UNKNOWN for downstream contracts. The model never decides contract behavior: validation, confidence bands, retry caps, storage writes, and can_pass() are deterministic. Evidence: primitive and consumer lint clean; 27 direct tests pass, 6 StudioNet integration tests pass covering every write and view plus a strict convergence check. StudioNet deploy at 0x1D4caB4b4C2a88538DAA68054834078Ed860fDEc: request_check created vsg-1, and resolve converged to PASS with HIGH confidence after several NO_MAJORITY retries.

## Character Count

The notes paragraph is 791 characters, counted programmatically with Python `len()`.

## Evidence Links

- GitHub repo: https://github.com/Ifem1/visual-state-gate
- Explorer contract page: https://explorer-studio.genlayer.com/contracts/0x1D4caB4b4C2a88538DAA68054834078Ed860fDEc
- Studio import: network `studionet`, contract address `0x1D4caB4b4C2a88538DAA68054834078Ed860fDEc`
