from backend.models import StorableModel


class DatabaseService:
    def __init__(self):
        self.tables = {}

    def _get_next_id(self) -> int:
        return max(self.memory.keys(), default=0) + 1

    def save(self, model: StorableModel) -> int:
        if hasattr(model, 'id'):
            model_id = model.id
        else:
            model_id = self._get_next_id()

        if model.table_name not in self.tables.keys():
            self.tables[model.table_name] = {}
        self.tables[model.table_name][model_id] = model
        return model_id

    def update(self, model_id, model: StorableModel):
        pass

    def get(self, table_name, model_id: int) -> dict | None:
        return self.tables.get(table_name, {}).get(model_id)

    def delete(self, table_name, model_id: int):
        self.tables.get(table_name, {}).pop(model_id)

    def find(self, table_name, **filters) -> list[dict]:
        found = filter(
            lambda m: all([m.get(name) == value for name, value in filters.items()]),
            self.tables.get(table_name, {}).values()
        )
        return list(found)

