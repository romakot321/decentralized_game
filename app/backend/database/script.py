from app.backend.database.models import Transaction
from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


class Operation(Enum):
    push = b'\x00'
    push_alt = b'\x01'
    verify_signature = b'\x02'
    check_equal = b'\x03'
    hash_top = b'\x04'
    duplicate_top = b'\x05'

    @classmethod
    def from_byte(cls, byte: bytes):
        for attrname in cls._member_names_:
            attr = getattr(cls, attrname)
            if attr.value == byte:
                return attr

    def operands_size(self, next_byte: bytes) -> list[int]:
        """Get operands size
        Positive - from script
        Negative - from stack or altstack. -1 = top element from stack, -2 from altstack
        String - from transaction
        """
        if self == Operation.push:
            return [1, int.from_bytes(next_byte, 'big')]
        if self == Operation.push_alt:
            return [-2]
        if self == Operation.verify_signature:
            return [-1, -1, 'encode']
        if self == Operation.check_equal:
            return [-1, -1]
        return []


@dataclass
class Command:
    operation: Operation
    operands: list


class ScriptError(Exception):
    pass


class ScriptService:
    def __init__(self, script: str, transaction: Transaction, altstack: list = None):
        """
        script: str - hex present of script
        """
        self._stack = []  # Runtime memory
        self._altstack = [] if altstack is None else altstack  # Arguments for script
        # Altstack is being formed from outputs of matched inputs
        self.script = bytes.fromhex(script) if isinstance(script, str) else script
        self.tx = transaction

    @classmethod
    def run_transaction(cls, transaction: Transaction, depends: dict[str, Transaction]) -> list[bool]:
        results: list[bool] = []
        altstack: list[bytes] = []
        for inp in transaction.inputs:
            refer_out = depends[inp.tx_id].outputs[inp.output_index]
            altstack.append(refer_out.value)
        for inp in transaction.inputs:
            refer_out = depends[inp.tx_id].outputs[inp.output_index]
            script = inp.unlock_script + refer_out.lock_script
            result = cls(script, depends[inp.tx_id], altstack.copy()).run()
            results.extend(result)
        return results

    @classmethod
    def get_transaction_depends(cls, transaction: Transaction) -> list[str]:
        """Return list of transactions ids which transaction refer to"""
        return [
            inp.tx_id
            for inp in transaction.inputs
        ]

    def execute_command(self, cmd: Command):
        if cmd.operation == Operation.push:
            self._stack.append(cmd.operands[1])
        elif cmd.operation == Operation.push_alt:
            self._stack.append(cmd.operands[0])
        elif cmd.operation == Operation.check_equal:
            if not cmd.operands[0] == cmd.operands[1]:
                raise ScriptError("Equal error")
        elif cmd.operation == Operation.hash_top:
            to_hash = self._stack.pop(-1)
            self._stack.append(sha256(to_hash).digest())
        elif cmd.operation == Operation.duplicate_top:
            self._stack.append(self._stack[-1])
        elif cmd.operation == Operation.verify_signature:
            pubkey = Ed25519PublicKey.from_public_bytes(cmd.operands[0])
            pubkey.verify(cmd.operands[1], cmd.operands[2])
            self._stack.append(True)

    def get_command_operands(self, operands_index: int, operation: Operation) -> tuple[list, int]:
        operands = []
        for opsize in operation.operands_size(self.script[operands_index:operands_index + 1]):
            if isinstance(opsize, str):
                op = getattr(self.tx, opsize)
                if callable(op):
                    op = op()
                operands.append(op)
            elif opsize >= 0:
                operands.append(self.script[operands_index:operands_index + opsize])
                operands_index += opsize
            elif opsize == -1:
                operands.append(self._stack.pop(-1))
            elif opsize == -2:
                operands.append(self._altstack.pop(-1))
        return operands, operands_index - 1

    def _run_script(self):
        i = -1
        while (i := i + 1) < len(self.script):
            operation = Operation.from_byte(self.script[i:i + 1])
            if operation is None:
                raise ScriptError(f"Invalid operation {self.script[i:i + 1]}")
            cmd = Command(operation=operation, operands=[])
            cmd.operands, i = self.get_command_operands(i + 1, operation)
            self.execute_command(cmd)
            #print(f"Byte {i}:")
            #print(f'\tCommand: {cmd}')
            #print(f'\tStack: {self._stack}')
        if not self._stack:
            self._stack.append(True)

    def run(self):
        self._run_script()
        return self._stack


if __name__ == '__main__':
    script = b'\x00\x02\x1a\x01\x00\x02\xaa\xaa\x02'.hex()
    service = ScriptService(script, None)
    service.run()

