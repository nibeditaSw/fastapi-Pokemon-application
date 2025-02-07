from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Pokemon(Base):
    __tablename__ = "pokemons"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    height = Column(Integer)
    weight = Column(Integer)
    xp = Column(Integer)
    image_url = Column(String)
    pokemon_url = Column(String)

    # Relationships
    abilities = relationship("Ability", back_populates="pokemons", cascade="all, delete")
    stats = relationship("Stat", back_populates="pokemons", cascade="all, delete")
    types = relationship("Type", back_populates="pokemons", cascade="all, delete")


class Ability(Base):
    __tablename__ = "abilities"
    
    id = Column(Integer, primary_key=True, index=True)
    pokemon_id = Column(Integer, ForeignKey("pokemons.id"))
    name = Column(String, nullable=False)
    is_hidden = Column(Boolean, default=False)

    pokemon = relationship("Pokemon", back_populates="abilities")


class Stat(Base):
    __tablename__ = "stats"
    
    id = Column(Integer, primary_key=True, index=True)
    pokemon_id = Column(Integer, ForeignKey("pokemons.id"))
    name = Column(String, nullable=False)
    base_stat = Column(Integer)

    pokemon = relationship("Pokemon", back_populates="stats")


class Type(Base):
    __tablename__ = "types"
    
    id = Column(Integer, primary_key=True, index=True)
    pokemon_id = Column(Integer, ForeignKey("pokemons.id"))
    name = Column(String, nullable=False)

    pokemon = relationship("Pokemon", back_populates="types")
