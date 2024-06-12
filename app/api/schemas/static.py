from pydantic import BaseModel, Field, AliasChoices


class Static(BaseModel):
    id: str = Field(validation_alias=AliasChoices('object_id', 'id'))
    position: tuple[int, int]

