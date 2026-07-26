# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

from genlayer import *


@gl.contract_interface
class IVisualStateGate:
    class View:
        def can_pass(self, request_id: str) -> bool: ...
        def verdict(self, request_id: str) -> str: ...
        def latest_request_for(self, consumer_key: str) -> str: ...

    class Write:
        def request_check(
            self, url: str, condition: str, subject: str, consumer_key: str
        ) -> str: ...


class VisualGateConsumer(gl.Contract):
    gate_address: Address
    consumer_key: str
    last_request_id: str
    unlocked: bool

    def __init__(self, gate_address: str, consumer_key: str = "demo-consumer"):
        self.gate_address = Address(gate_address)
        self.consumer_key = consumer_key
        self.last_request_id = ""
        self.unlocked = False

    @gl.public.write
    def ask_gate(self, url: str, condition: str, subject: str = "") -> None:
        gate = IVisualStateGate(self.gate_address)
        self.last_request_id = gate.emit().request_check(
            url, condition, subject, self.consumer_key
        )

    @gl.public.write
    def sync_unlock(self) -> None:
        if self.last_request_id == "":
            raise gl.vm.UserError("no request")
        gate = IVisualStateGate(self.gate_address)
        if not gate.view().can_pass(self.last_request_id):
            raise gl.vm.UserError("gate has not passed")
        self.unlocked = True

    @gl.public.view
    def status(self) -> dict:
        gate = IVisualStateGate(self.gate_address)
        verdict = "UNKNOWN"
        if self.last_request_id != "":
            verdict = gate.view().verdict(self.last_request_id)
        return {
            "consumer_key": self.consumer_key,
            "last_request_id": self.last_request_id,
            "verdict": verdict,
            "unlocked": self.unlocked,
        }
