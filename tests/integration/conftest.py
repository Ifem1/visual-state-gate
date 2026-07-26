import pytest

from gltest import get_contract_factory
from gltest.assertions import tx_execution_failed

RESOLVE_WAIT_INTERVAL = 5000
RESOLVE_WAIT_RETRIES = 90


@pytest.fixture(scope="module")
def gate_factory():
    return get_contract_factory(contract_file_path="visual_state_gate.py")


@pytest.fixture(scope="module")
def gate(gate_factory):
    return gate_factory.deploy(
        args=[1000, 3, 320, 600, 160, 500],
        wait_interval=RESOLVE_WAIT_INTERVAL,
        wait_retries=RESOLVE_WAIT_RETRIES,
    )


def resolve_until_settled(contract, request_id: str, max_network_retries: int = 8):
    """
    Retries the resolve() transaction itself, not the contract's own attempt
    counter. StudioNet consensus rounds can return CANCELED/NO_MAJORITY or
    UNDETERMINED with nothing written and the transaction reported as failed;
    that is documented, expected flakiness, not a contract bug, so this loop
    re-submits until a round actually lands or the retry budget is spent.
    """
    last_receipt = None
    for _ in range(max_network_retries):
        last_receipt = contract.resolve(args=[request_id]).transact(
            wait_interval=RESOLVE_WAIT_INTERVAL,
            wait_retries=RESOLVE_WAIT_RETRIES,
        )
        if not tx_execution_failed(last_receipt):
            return last_receipt
    return last_receipt
