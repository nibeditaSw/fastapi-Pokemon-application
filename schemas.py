from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class Ability(BaseModel):
    name: str
    is_hidden: bool

    # class Config:
    #     orm_mode = True


class Stat(BaseModel):
    name: str
    base_stat: int = 0

    # class Config:
    #     orm_mode = True


class Type(BaseModel):
    name: str

    # class Config:
    #     orm_mode = True


class PokemonModel(BaseModel):
    id: int = Field(..., ge=1, description="ID must be a positive integer.")
    name: str
    height: Optional[int] = 0
    weight: Optional[int] = 0
    xp: Optional[int] = 0
    image_url: Optional[HttpUrl]
    pokemon_url: Optional[HttpUrl]
    abilities: List[Ability]
    stats: List[Stat]
    types: List[Type]

    class Config:
        orm_mode = True


class PokemonUpdateModel(BaseModel):
    name: str
    height: Optional[int] = 0
    weight: Optional[int] = 0
    xp: Optional[int] = 0
    image_url: Optional[HttpUrl]
    pokemon_url: Optional[HttpUrl]
    abilities: Optional[List[Ability]]
    stats: Optional[List[Stat]]
    types: Optional[List[Type]]

    class Config:
        orm_mode = True
