import json 
import logging
import urllib.request 
from fastapi import FastAPI, HTTPException 
from typing import Dict
from schemas import PokemonModel, PokemonUpdateModel


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
data_cache: Dict[int, Dict] = {} 



@app.on_event("startup") 
def load_data(): 
    """
    Loads Pokémon data from a specified URL into the in-memory cache.

    This function is triggered on application startup. It retrieves Pokémon data
    from a remote JSON source, processes it, and stores it in the global data_cache
    for quick access. In case of any errors during the data loading process, an
    appropriate error message is logged, and a RuntimeError is raised.

    Raises:
        RuntimeError: If there is an error while loading or processing the data.
    """
    global data_cache 
    try:

        with urllib.request.urlopen(data_url) as response: 
            data = json.loads(response.read().decode()) 
            data_cache = {int(pokemon["id"]): pokemon for pokemon in data}
            logging.info("Successfully loaded Pokémon data from the URL.")

    except Exception as e: 
        logging.error(f"Failed to load Pokémon data: {e}")
        raise RuntimeError(f"Failed to load Pokémon data: {e}") 


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



@app.get("/pokemon/{pokemon_id}") 
def get_pokemon_by_id(pokemon_id: int): 
    """
    Retrieves a Pokémon by its ID.

    This endpoint fetches a Pokémon from the in-memory data cache using its unique ID.
    If the Pokémon is found, it returns the corresponding data. If not, a 404 error is raised.

    Parameters:
        pokemon_id (int): The unique ID of the Pokémon to retrieve.

    Returns:
        Dict[str, Any]: The data of the Pokémon if found.

    Raises:
        HTTPException: If the Pokémon is not found, a 404 error is raised.
    """
    if pokemon_id in data_cache: 
        logging.info(f"Successfully retrieved Pokémon with ID: {pokemon_id}")
        return data_cache[pokemon_id] 
    else:
        logging.error(f"Failed to find Pokémon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokémon not found") 



@app.get("/pokemon/name/{pokemon_name}")
def get_pokemon_by_name(pokemon_name: str):
    """
    Retrieves a Pokémon by its name.

    This endpoint fetches a Pokémon from the in-memory data cache using its name.
    If the Pokémon is found, it returns the corresponding data. If not, a 404 error is raised.

    Parameters:
        pokemon_name (str): The name of the Pokémon to retrieve.

    Returns:
        Dict[str, Any]: The data of the Pokémon if found.

    Raises:
        HTTPException: If the Pokémon is not found, a 404 error is raised.
    """
    for pokemon in data_cache.values():

        if pokemon["name"].lower() == pokemon_name.lower():
            logging.info(f"Successfully retrieved Pokémon with name: {pokemon_name}")
            return pokemon
    logging.warning(f"Failed to find Pokémon with name: {pokemon_name}")    
    raise HTTPException(status_code=404, detail="Pokémon not found")



@app.post("/pokemon/")
def create_pokemon(pokemon: PokemonModel):
    """
    Creates a new Pokémon in the in-memory data cache.

    This endpoint creates a new Pokémon from the input data and stores it in the
    in-memory data cache. If a Pokémon with the same ID already exists, a 400
    error is raised.

    Parameters:
        pokemon (PokemonModel): The Pokémon data to add.

    Returns:
        Dict[str, Any]: A dictionary containing a success message and the
            created Pokémon.

    Raises:
        HTTPException: If the Pokémon with the same ID already exists, a 400
            error is raised.
    """
    if pokemon.id in data_cache:
        logging.warning(f"Attempt to create Pokémon with existing ID: {pokemon.id}")
        raise HTTPException(status_code=400, detail="Pokémon with this ID already exists.")
    data_cache[pokemon.id] = pokemon.dict()
    logging.info(f"Successfully created Pokémon with ID: {pokemon.id}")
    return {"message": "Pokémon added successfully", "pokemon": pokemon}



@app.put("/pokemon/{pokemon_id}")
def update_pokemon(pokemon_id: int, updated_data: PokemonUpdateModel):
    """
    Updates an existing Pokémon in the in-memory data cache.

    This endpoint updates the data of an existing Pokémon identified by its ID.
    The updated data is provided in the request body. If the Pokémon is not found,
    a 404 error is raised. The ID of the Pokémon cannot be changed during the update.

    Parameters:
        pokemon_id (int): The unique ID of the Pokémon to update.
        updated_data (PokemonUpdateModel): The updated data for the Pokémon.

    Returns:
        Dict[str, Any]: A dictionary containing a success message and the updated Pokémon data.

    Raises:
        HTTPException: If the Pokémon is not found, a 404 error is raised.
    """
    if pokemon_id not in data_cache:
        logging.warning(f"Attempt to update non-existing Pokémon with ID: {pokemon_id}")
        raise HTTPException(status_code=404, detail="Pokémon not found")
    
    # Prevent ID changes during updates
    existing_data = data_cache[pokemon_id]
    updated_data_dict = updated_data.dict()
    updated_data_dict["id"] = existing_data["id"]

    data_cache[pokemon_id] = updated_data_dict
    logging.info(f"Successfully updated Pokémon with ID: {pokemon_id}")
    return {"message": "Pokémon updated successfully", "pokemon": data_cache[pokemon_id]}



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
    