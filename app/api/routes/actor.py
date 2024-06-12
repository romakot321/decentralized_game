from fastapi import APIRouter, Depends

from app.api.schemas import ActorMakeSchema
from app.api.schemas import ActorSchema
from app.api.schemas import ActorEventSchema
from app.api.services.actor import ActorService

router = APIRouter(prefix='/actor', tags=["Actor"])


@router.post('', response_model=ActorSchema)
def make(schema: ActorMakeSchema, service: ActorService = Depends()):
    return service.make(schema)


@router.post('/event', status_code=201)
def handle_event(schema: ActorEventSchema, service: ActorService = Depends()):
    """Return id of maked transaction"""
    tx = service.handle_event(schema)
    return tx.id if tx else None


@router.get('')
def get_actors(service: ActorService = Depends()):
    return service.get_actors()


@router.get('/{address}')
def get_actor(address: str, service: ActorService = Depends()):
    return service.get_actor(address)

