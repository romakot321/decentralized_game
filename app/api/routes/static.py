from fastapi import APIRouter, Depends
from app.api.schemas import Static
from app.api.services.static import StaticService


router = APIRouter(prefix='/static', tags=['Static'])


@router.get('', response_model=list[Static])
def get_static_objects(service: StaticService = Depends()):
    return service.get_many()

