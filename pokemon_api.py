import json 
import logging
import urllib.request 
from fastapi import FastAPI, HTTPException, Depends 
from typing import Dict, List
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

# In-memory storage for Pokemon data
data_cache: Dict[int, Dict] = {} 



@app.on_event("startup")
def load_data(): 
    """
    Load Pokemon data from a remote JSON dataset into the database at startup.

    This function is triggered on the application's startup event. It retrieves
    Pokemon data from a specified URL, parses the JSON response, and populates
    the database with Pokemon details, including abilities, stats, and types.

    The function checks for the existence of each Pokemon in the database to
    avoid duplicates. If a Pokemon does not exist, it is added along with its
    associated abilities, stats, and types.

    In case of any errors during the data loading process, an error message is
    printed.

    Raises:
        Exception: If there is any error during the data retrieval or database
        operations.
    """
    try:
        with urllib.request.urlopen(data_url) as response:
            data = json.loads(response.read().decode())
        
        db: Session = next(get_db())
        for p in data:
            if not db.query(Pokemon).filter(Pokemon.id == p["id"]).first():
                # Add Pokemon
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
    return {"message": "Welcome to the Pokemon Lookup API!"} 


@app.get("/pokemon/all", response_model=List[PokemonModel])
def get_all_pokemon(db: Session = Depends(get_db)):
    """
    Retrieve all Pokemon.

    This endpoint fetches the details of all Pokemon stored in the database.
    Each Pokemon's attributes include its name, height, weight, experience points,
    as well as associated abilities, stats, and types.

    Args:
        db (Session, optional): The database session dependency.

    Returns:
        List[PokemonModel]: A list of Pokemon details.

    Raises:
        HTTPException: If no Pokemon data is found, a 404 error is raised with
        a message indicating that no Pokemon are available.
    """

    pokemon_list = db.query(Pokemon).all()
    if pokemon_list:
        logging.info(f"Successfully retrieved {len(pokemon_list)} Pokemon from the database.")
        return pokemon_list
    else:
        logging.error("No Pokemon found in the database.")
        raise HTTPException(status_code=404, detail="No Pokemon found")




@app.get("/pokemon/{pokemon_id}", response_model=PokemonModel) 
def get_pokemon_by_id(pokemon_id: int, db: Session = Depends(get_db)): 
    
    """
    Retrieve a Pokemon by its ID.

    This endpoint fetches the details of a specific Pokemon from the database
    using the provided Pokemon ID. The response includes the Pokemon's attributes
    such as its name, height, weight, experience points, and associated abilities,
    stats, and types.

    Args:
        pokemon_id (int): The ID of the Pokemon to retrieve.
        db (Session, optional): The database session dependency.

    Returns:
        PokemonModel: The Pokemon details if found.

    Raises:
        HTTPException: If the Pokemon is not found, a 404 error is raised with
        a message indicating that the Pokemon was not found.
    """

    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if pokemon:
        logging.info(f"Successfully retrieved Pokemon with ID: {pokemon_id}")
        return pokemon
    else:
        logging.error(f"Failed to find Pokemon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokemon not found")
    

@app.get("/pokemon/name/{pokemon_name}", response_model=PokemonModel)
def get_pokemon_by_name(pokemon_name: str, db: Session = Depends(get_db)):
    
    """
    Retrieve a Pokemon by its name.

    This endpoint fetches the details of a specific Pokemon from the database
    using the provided Pokemon name. The response includes the Pokemon's attributes
    such as its name, height, weight, experience points, and associated abilities,
    stats, and types.

    Args:
        pokemon_name (str): The name of the Pokemon to retrieve.
        db (Session, optional): The database session dependency.

    Returns:
        PokemonModel: The Pokemon details if found.

    Raises:
        HTTPException: If the Pokemon is not found, a 404 error is raised with
        a message indicating that the Pokemon was not found.
    """
    
    pokemon = db.query(Pokemon).filter(Pokemon.name.ilike(pokemon_name)).first()
    if pokemon:
        logging.info(f"Successfully retrieved Pokemon with name: {pokemon_name}")
        return pokemon
    else:
        logging.error(f"Failed to find Pokemon with name: {pokemon_name}")
        raise HTTPException(status_code=404, detail="Pokemon not found")


@app.post("/pokemon/", response_model=PokemonModel)
def create_pokemon(pokemon: PokemonModel, db: Session = Depends(get_db)):
    
    """
    Create a new Pokemon entry.

    This endpoint allows for the creation of a new Pokemon in the database. It
    takes a Pokemon model as input and adds the corresponding Pokemon details,
    including attributes, abilities, stats, and types, to the database.

    Args:
        pokemon (PokemonModel): An instance of the Pokemon model containing the
            details of the Pokemon to be created.
        db (Session): The database session dependency.

    Returns:
        Dict: A dictionary containing the created Pokemon's details, including
        attributes such as ID, name, height, weight, experience points, image URL,
        Pokemon URL, abilities, stats, and types.

    Raises:
        HTTPException: If a Pokemon with the specified ID already exists, a 400
        error is raised with a message indicating the duplication.
    """

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
    
    """
    Update a Pokemon entry.

    This endpoint allows for the partial update of an existing Pokemon in the
    database. It takes a Pokemon ID and an instance of the Pokemon update model
    containing the updated details of the Pokemon. The response includes the
    updated Pokemon's details, including attributes, abilities, stats, and types.

    Args:
        pokemon_id (int): The ID of the Pokemon to update.
        updated_data (PokemonUpdateModel): An instance of the Pokemon update model
            containing the updated details of the Pokemon.
        db (Session): The database session dependency.

    Returns:
        PokemonUpdateModel: The updated Pokemon's details, including attributes
            such as ID, name, height, weight, experience points, image URL,
            Pokemon URL, abilities, stats, and types.

    Raises:
        HTTPException: If the Pokemon is not found, a 404 error is raised with
            a message indicating that the Pokemon was not found.
    """
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
    
    """
    Delete a Pokemon entry.

    This endpoint deletes an existing Pokemon from the database using the provided
    Pokemon ID. If the Pokemon is found, it is removed from the database, and a
    confirmation message is logged.

    Args:
        pokemon_id (int): The ID of the Pokemon to delete.
        db (Session): The database session dependency.

    Returns:
        Pokemon: The deleted Pokemon's details if found.

    Raises:
        HTTPException: If the Pokemon is not found, a 404 error is raised with
        a message indicating that the Pokemon was not found.
    """

    pokemon = db.query(Pokemon).filter(Pokemon.id == pokemon_id).first()
    if not pokemon:
        logging.warning(f"Attempt to delete non-existing Pokemon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokemon not found")

    db.delete(pokemon)
    db.commit()
    logging.info(f"Successfully deleted Pokemon with ID: {pokemon_id}")
    return pokemon
