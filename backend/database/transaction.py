from backend.database.models import Transaction
from backend.database.models import MoveTransaction, TransactionsAction
from backend.database.models import PickTransaction, _action_to_transaction_class

from enum import Enum


class TransactionRepository:
    """Implements transactions pool"""

    def __init__(self, db_service):
        self.db_service = db_service

    def make(self, actor_id, data: Transaction.TransactionData, action: TransactionsAction):
        trans_cls = _action_to_transaction_class.get(action)
        if trans_cls is None:
            raise ValueError("Invalid transaction action")
        data_packed = trans_cls.pack_data(data)
        return trans_cls(
            actor=actor_id,
            data=data_packed
        )

    def store(self, transaction: Transaction):
        self.db_service.save(transaction)

    def get_many(self, **filters):
        return self.db_service.find(Transaction.table_name, **filters)

    def delete(self, transaction_id):
        self.db_service.delete(Transaction.table_name, transaction_id)

    def clear(self):
        for trans in self.get_many():
            self.delete(trans.id)

