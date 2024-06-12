from app.api.services.actor import ActorService
from app.api.services.static import StaticService
from app.api import routes

import inspect
from fastapi import FastAPI


class APIRepository:
    def __init__(self, backend_repository):
        ActorService.backend_repository = backend_repository
        StaticService.backend_repository = backend_repository
        self.app = None

    def init(self) -> FastAPI:
        self.app = FastAPI()

        for _, route in inspect.getmembers(routes, inspect.ismodule):
            self.app.include_router(route.router)

        return self.app

