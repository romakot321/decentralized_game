from app.api.schemas import Static

from fastapi import HTTPException


class StaticService:
    backend_repository = None

    def get_many(self) -> list[Static]:
        return self.backend_repository.get_static_objects_positions()

