from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class Ability(BaseModel):
    name: str
    is_hidden: bool


class Stat(BaseModel):
    name: str
    base_stat: int = 0


class Type(BaseModel):
    name: str


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


class PokemonUpdateModel(BaseModel):
    name: str
    height: Optional[int] = 0
    weight: Optional[int] = 0
    xp: Optional[int] = 0
    image_url: Optional[HttpUrl]
    pokemon_url: Optional[HttpUrl]
    abilities: List[Ability]
    stats: List[Stat]
    types: List[Type]
