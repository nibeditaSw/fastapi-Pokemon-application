import json 
import logging
import urllib.request 
from fastapi import FastAPI, HTTPException, Depends 
from typing import Dict
from sqlalchemy.orm import Session
from pydantic.networks import HttpUrl
from schemas import PokemonModel, PokemonUpdateModel
from database import Base, engine, get_db
from models import Pokemon, Ability, Stat, Type


# Configure logging
logging.basicConfig(
    # filename="pokemon.log",
    # filemode="a",
    format="{asctime} | {levelname} | {message}",
    datefmt="%d-%b-%y %H:%M:%S",
    level=10,
    style="{"
)

# Initialize the database
Base.metadata.create_all(bind=engine)

# URL for the dataset
data_url = "https://raw.githubusercontent.com/DetainedDeveloper/Pokedex/master/pokedex_raw/pokedex_raw_array.json" 

# Initialize FastAPI app
app = FastAPI() 

# In-memory storage for Pokémon data
data_cache: Dict[int, Dict] = {} 



@app.on_event("startup")
def load_data():
    """
    Load Pokémon data into the database when the app starts.
    """
    try:
        with urllib.request.urlopen(data_url) as response:
            data = json.loads(response.read().decode())
        
        db: Session = next(get_db())
        for p in data:
            if not db.query(Pokemon).filter(Pokemon.id == p["id"]).first():
                # Add Pokémon
                pokemon = Pokemon(
                    id=p["id"],
                    name=p["name"],
                    height=p["height"],
                    weight=p["weight"],
                    xp=p["xp"],
                    image_url=p["image_url"],
                    pokemon_url=p["pokemon_url"]
                )
                db.add(pokemon)

                # Add abilities
                for ab in p["abilities"]:
                    ability = Ability(
                        name=ab["name"],
                        is_hidden=ab["is_hidden"],
                        pokemon=pokemon
                    )
                    db.add(ability)

                # Add stats
                for st in p["stats"]:
                    stat = Stat(
                        name=st["name"],
                        base_stat=st["base_stat"],
                        pokemon=pokemon
                    )
                    db.add(stat)

                # Add types
                for t in p["types"]:
                    type_ = Type(
                        name=t["name"],
                        pokemon=pokemon
                    )
                    db.add(type_)

        db.commit()
    except Exception as e:
        print(f"Error loading data: {e}")


@app.get("/") 
def root(): 
    """
    The root endpoint of the API.

    This endpoint is used to check if the API is up and running. It returns a
    simple message indicating that the API is available.

    Returns:
        Dict[str, str]: A dictionary containing a welcome message.
    """
    logging.info("API root endpoint accessed.")
    return {"message": "Welcome to the Pokémon Lookup API!"} 



@app.get("/pokemon/{pokemon_id}", response_model=PokemonModel) 
def get_pokemon_by_id(pokemon_id: int, db: Session = Depends(get_db)): 
    
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if pokemon:
        logging.info(f"Successfully retrieved Pokemon with ID: {pokemon_id}")
        return pokemon
    else:
        logging.error(f"Failed to find Pokemon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokemon not found")
    

@app.get("/pokemon/name/{pokemon_name}", response_model=PokemonModel)
def get_pokemon_by_name(pokemon_name: str, db: Session = Depends(get_db)):
    
    pokemon = db.query(Pokemon).filter(Pokemon.name.ilike(pokemon_name)).first()
    if pokemon:
        logging.info(f"Successfully retrieved Pokemon with name: {pokemon_name}")
        return pokemon
    else:
        logging.error(f"Failed to find Pokemon with name: {pokemon_name}")
        raise HTTPException(status_code=404, detail="Pokemon not found")


@app.post("/pokemon/", response_model=PokemonModel)
def create_pokemon(pokemon: PokemonModel, db: Session = Depends(get_db)):
    
    existing_pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon.id).first()
    if existing_pokemon:
        logging.warning(f"Attempt to create Pokemon with existing ID: {pokemon.id}")
        raise HTTPException(status_code=400, detail="Pokemon with this ID already exists.")
    
    # Convert HttpUrl fields to strings
    image_url = str(pokemon.image_url) if isinstance(pokemon.image_url, HttpUrl) else pokemon.image_url
    pokemon_url = str(pokemon.pokemon_url) if isinstance(pokemon.pokemon_url, HttpUrl) else pokemon.pokemon_url

    # Create an instance of the ORM model
    new_pokemon = Pokemon(
        id=pokemon.id,
        name=pokemon.name,
        height=pokemon.height,
        weight=pokemon.weight,
        xp=pokemon.xp,
        image_url=image_url,
        pokemon_url=pokemon_url
    )
     # Add abilities, stats, and types
    new_pokemon.abilities = [
        Ability(name=ability.name, is_hidden=ability.is_hidden) for ability in pokemon.abilities
    ]
    new_pokemon.stats = [
        Stat(name=stat.name, base_stat=stat.base_stat) for stat in pokemon.stats
    ]
    new_pokemon.types = [
        Type(name=type_.name) for type_ in pokemon.types
    ]

    db.add(new_pokemon)
    db.commit()
    db.refresh(new_pokemon)
    # serialize the data for the response
    response = {
        "id": new_pokemon.id,
        "name": new_pokemon.name,
        "height": new_pokemon.height,
        "weight": new_pokemon.weight,
        "xp": new_pokemon.xp,
        "image_url": new_pokemon.image_url,
        "pokemon_url": new_pokemon.pokemon_url,
        "abilities": [{"name": a.name, "is_hidden": a.is_hidden} for a in new_pokemon.abilities],
        "stats": [{"name": s.name, "base_stat": s.base_stat} for s in new_pokemon.stats],
        "types": [{"name": t.name} for t in new_pokemon.types],
    }

    logging.info(f"Successfully created pokemon with ID: {pokemon.id}")
    return response
    


@app.put("/pokemon/{pokemon_id}", response_model=PokemonUpdateModel)
def update_pokemon(pokemon_id: int, updated_data: PokemonUpdateModel, db: Session = Depends(get_db)):
    
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if not pokemon:
        logging.warning(f"Attempt to update non-existing Pokemon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokemon not found")
    
    for key, value in updated_data.dict(exclude_unset=True, exclude={"abilities", "stats", "types"}).items():
        # Convert HttpUrl to string if needed
        if isinstance(value, HttpUrl):
            value = str(value)
        setattr(pokemon, key, value)

     # Update abilities
    if updated_data.abilities is not None:
        # Clear existing abilities
        db.query(Ability).filter(Ability.pokemon_id == pokemon_id).delete()
        # Add new abilities
        for ability_data in updated_data.abilities:
            new_ability = Ability(**ability_data.dict(), pokemon_id=pokemon_id)
            db.add(new_ability)

    # Update stats
    if updated_data.stats is not None:
        # Clear existing stats
        db.query(Stat).filter(Stat.pokemon_id == pokemon_id).delete()
        # Add new stats
        for stat_data in updated_data.stats:
            new_stat = Stat(**stat_data.dict(), pokemon_id=pokemon_id)
            db.add(new_stat)

    # Update types
    if updated_data.types is not None:
        # Clear existing types
        db.query(Type).filter(Type.pokemon_id == pokemon_id).delete()
        # Add new types
        for type_data in updated_data.types:
            new_type = Type(**type_data.dict(), pokemon_id=pokemon_id)
            db.add(new_type)

    db.commit()
    db.refresh(pokemon)
    logging.info(f"Successfully updated Pokemon with ID: {pokemon_id}")
    return pokemon



@app.delete("/pokemon/{pokemon_id}")
def delete_pokemon(pokemon_id: int, db: Session = Depends(get_db)):
    
    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if not pokemon:
        logging.warning(f"Attempt to delete non-existing Pokemon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokemon not found")

    db.delete(pokemon)
    db.commit()
    logging.info(f"Successfully deleted Pokemon with ID: {pokemon_id}")
    return pokemon
