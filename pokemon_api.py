import json 
import logging
import urllib.request 
from fastapi import FastAPI, HTTPException 
from typing import Dict
from schemas import PokemonSchema


# Configure logging
logging.basicConfig(
    # filename="pokemon.log",
    # filemode="a",
    format="{asctime} | {levelname} | {message}",
    datefmt="%d-%b-%y %H:%M:%S",
    level=10,
    style="{"
)

# URL for the dataset
data_url = "https://raw.githubusercontent.com/DetainedDeveloper/Pokedex/master/pokedex_raw/pokedex_raw_array.json" 

# Initialize FastAPI app
app = FastAPI() 

# In-memory storage for Pokémon data
data_cache: Dict[int, PokemonSchema] = {} 



@app.on_event("startup") 
def load_data(): 
    """
    Loads the Pokémon data into memory from the dataset URL when the FastAPI app starts.

    This function is invoked when the FastAPI app starts. It attempts to load the Pokémon data from the dataset URL into memory. If the data is successfully loaded, it is stored in the `data_cache` variable. If the data fails to load, a `RuntimeError` is raised.

    Parameters:
    None

    Returns:
    None

    Raises:
    RuntimeError: If the data fails to load from the URL.
    """
   
    global data_cache 
    try:

        with urllib.request.urlopen(data_url) as response: 
            data = json.loads(response.read().decode()) 
            data_cache = {int(pokemon["id"]): PokemonSchema(**pokemon) for pokemon in data}
            logging.info("Successfully loaded Pokémon data from the URL.")

    except Exception as e: 
        logging.error(f"Failed to load Pokémon data: {e}")
        raise RuntimeError(f"Failed to load Pokémon data: {e}") 


@app.get("/") 
def root(): 
    """
    Endpoint to test the API's health.

    This endpoint simply returns a welcome message to test whether the API is working correctly.

    Parameters:
    None

    Returns:
    Dict[str, str]: A dictionary with a single key "message" containing a welcome message.

    Raises:
    None
    """
    logging.info("API root endpoint accessed.")
    return {"message": "Welcome to the Pokémon Lookup API!"} 


@app.get("/pokemon/{pokemon_id}", response_model=PokemonSchema) 
def get_pokemon_by_id(pokemon_id: int): 
    
    """
    Endpoint to retrieve a Pokémon by its ID.

    This endpoint retrieves a Pokémon by its ID from the in-memory cache. If the Pokémon is found, it is returned in the response. If the Pokémon is not found, a 404 error is raised.

    Parameters:
    pokemon_id (int): The ID of the Pokémon to retrieve.

    Returns:
    PokemonSchema: The retrieved Pokémon.

    Raises:
    HTTPException: If the Pokémon is not found, a 404 error is raised.
    """
    
    if pokemon_id in data_cache: 
        logging.info(f"Successfully retrieved Pokémon with ID: {pokemon_id}")
        return data_cache[pokemon_id] 
    
    logging.error(f"Failed to find Pokémon with ID: {pokemon_id}")
    raise HTTPException(status_code=404, detail="Pokémon not found") 


@app.get("/pokemon/name/{pokemon_name}", response_model=PokemonSchema)
def get_pokemon_by_name(pokemon_name: str):
    
    """
    Endpoint to retrieve a Pokémon by its name.

    This endpoint retrieves a Pokémon by its name from the in-memory cache. If the Pokémon is found, it is returned in the response. If the Pokémon is not found, a 404 error is raised.

    Parameters:
    pokemon_name (str): The name of the Pokémon to retrieve.

    Returns:
    PokemonSchema: The retrieved Pokémon.

    Raises:
    HTTPException: If the Pokémon is not found, a 404 error is raised.
    """

    for pokemon in data_cache.values():

        if pokemon.name.lower() == pokemon_name.lower():
            logging.info(f"Successfully retrieved Pokémon with name: {pokemon_name}")
            return pokemon
    logging.warning(f"Failed to find Pokémon with name: {pokemon_name}")    
    raise HTTPException(status_code=404, detail="Pokémon not found")


@app.post("/pokemon/", response_model=PokemonSchema)
def create_pokemon(pokemon: PokemonSchema):

    """
    Endpoint to create a new Pokémon.

    This endpoint creates a new Pokémon and stores it in the in-memory cache. If the Pokémon is successfully created, it is returned in the response. If a Pokémon with the same ID already exists, a 400 error is raised.

    Parameters:
    pokemon (PokemonSchema): The Pokémon to create.

    Returns:
    PokemonSchema: The created Pokémon.

    Raises:
    HTTPException: If a Pokémon with the same ID already exists, a 400 error is raised.
    """
    if pokemon.id in data_cache:
        logging.warning(f"Attempt to create Pokémon with existing ID: {pokemon.id}")
        raise HTTPException(status_code=400, detail="Pokémon with this ID already exists.")
    data_cache[pokemon.id] = pokemon
    logging.info(f"Successfully created Pokémon with ID: {pokemon.id}")
    return pokemon




@app.put("/pokemon/{pokemon_id}", response_model=PokemonSchema)
def update_pokemon(pokemon_id: int, updated_data: PokemonSchema):
   
    """
    Endpoint to update an existing Pokémon's data.

    This endpoint updates the data of an existing Pokémon in the in-memory cache. If the Pokémon is found, its data is updated and returned in the response. If the Pokémon is not found, a 404 error is raised.

    Parameters:
    pokemon_id (int): The ID of the Pokémon to update.
    updated_data (PokemonSchema): The updated data for the Pokémon.

    Returns:
    PokemonSchema: The updated Pokémon.

    Raises:
    HTTPException: If the Pokémon is not found, a 404 error is raised.
    """

    if pokemon_id not in data_cache:
        logging.warning(f"Attempt to update non-existing Pokémon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokémon not found")
    data_cache[pokemon_id] = updated_data
    logging.info(f"Successfully updated Pokémon with ID: {pokemon_id}")
    return updated_data



@app.delete("/pokemon/{pokemon_id}")
def delete_pokemon(pokemon_id: int):
    
    """
    Endpoint to delete a Pokémon by its ID.

    This endpoint deletes a Pokémon by its ID from the in-memory cache. If the Pokémon is found, it is deleted and a success message is returned. If the Pokémon is not found, a 404 error is raised.

    Parameters:
    pokemon_id (int): The ID of the Pokémon to delete.

    Returns:
    Dict[str, Any]: A dictionary containing a success message and the deleted Pokémon.

    Raises:
    HTTPException: If the Pokémon is not found, a 404 error is raised.
    """
    if pokemon_id not in data_cache:
        logging.warning(f"Attempt to delete non-existing Pokémon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokémon not found")
    deleted_pokemon = data_cache.pop(pokemon_id)
    logging.info(f"Successfully deleted Pokémon with ID: {pokemon_id}")
    return {"message": "Pokémon deleted successfully", "pokemon": deleted_pokemon}
    