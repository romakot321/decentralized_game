from app.backend.database.models import StorableModel
import pickle
import os

DB_FILENAME = os.getenv('DB_FILENAME', 'db')


class DatabaseService:
    def __init__(self):
        self.tables = {}
        try:
            with open(DB_FILENAME, 'rb') as f:
                self.tables = dict(pickle.load(f))
        except (FileNotFoundError, EOFError):
            pass

    def _get_next_id(self, table_name) -> int:
        return max(self.tables.get(table_name, {}).keys(), default=0) + 1

    def save(self, model: StorableModel) -> int:
        if hasattr(model, 'id'):
            model_id = model.id
        else:
            model_id = self._get_next_id(model.table_name)
            model.id = model_id

        if model.table_name not in self.tables.keys():
            self.tables[model.table_name] = {}
        self.tables[model.table_name][model_id] = model
        with open(DB_FILENAME, 'wb') as f:
            pickle.dump(list(self.tables.items()), f)
        return model_id

    def update(self, model_id, model: StorableModel):
        self.tables[model.table_name][model_id] = model

    def get(self, table_name, model_id: int) -> dict | None:
        return self.tables.get(table_name, {}).get(model_id)

    def delete(self, table_name, model_id: int):
        try:
            return self.tables.get(table_name, {}).pop(model_id)
        except KeyError:
            return

    @staticmethod
    def _filter(objects, **filters):
        return filter(
             lambda m: all([getattr(m, name, None) == value for name, value in filters.items()]),
             objects
        )

    def find(self, table_name, subfilters: dict[str, dict] = None, **filters) -> list[dict]:
        found = list(self._filter(
            list(self.tables.get(table_name, {}).values()).copy(),
            **filters
        ))
        if subfilters:
            for attr, attr_filters in subfilters.items():
                for obj in found.copy():
                    if not list(self._filter(getattr(obj, attr, []), **attr_filters)):
                        found.remove(obj)
        return found

