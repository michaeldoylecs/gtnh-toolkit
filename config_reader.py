from typing import Dict, Optional
from pydantic.dataclasses import dataclass as pdataclass
import json
from pydantic import ValidationError
import yaml
import args
from gamelogic.electricity import Voltage, VoltageTier
from gamelogic.items import make_itemstack
from gamelogic.machines import StandardOverclockMachineRecipe, MachineRecipe, PerfectOverclockMachineRecipe
from gamelogic.game_time import GameTime
from models import FactoryConfig, TargetRate, make_target
import os

def normalize_machine_name(machine_name: str) -> str:
    normalized_name_map = {
        'Electric Blast Furnace': [
            'electric blast furnace',
            'ebf',
        ],
        'Large Chemical Reactor': [
            'large chemical reactor',
            'lcr',
        ],
    }

    inverted_map = {}
    for key, value_list in normalized_name_map.items():
        for value in value_list:
            inverted_map[value] = key

    normalized_name = inverted_map.get(machine_name.lower())
    if normalized_name is None:
        return machine_name
    else:
        return normalized_name

type AnyMachineRecipe = StandardOverclockMachineRecipe | PerfectOverclockMachineRecipe

# Define a mapping from machine name identifiers to recipe classes
# Using uppercase keys for case-insensitive matching later
MACHINE_NAME_TO_RECIPE_CLASS: dict[str, type[AnyMachineRecipe]] = {
    "Electric Blast Furnace": StandardOverclockMachineRecipe,
    "Large Chemical Reactor": PerfectOverclockMachineRecipe,
}

@pdataclass
class InputRecipe:
    m: str
    tier: str
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    dur: int
    eut: int

@pdataclass
class InputFactoryConfig:
    recipes: list[InputRecipe]
    targets: Dict[str, float]

def initialize_recipe(raw_recipe: InputRecipe) -> MachineRecipe:
    name = normalize_machine_name(raw_recipe.m)
    voltage_tier = VoltageTier.from_name(raw_recipe.tier.upper())
    inputs = [make_itemstack(item, quantity) for (item, quantity) in raw_recipe.inputs.items()]
    outputs = [make_itemstack(item, quantity) for (item, quantity) in raw_recipe.outputs.items()]
    duration = GameTime.from_ticks(raw_recipe.dur)
    eu_per_gametick = Voltage(raw_recipe.eut)

    if args.is_verbose():
            print(f"""
initialize_recipe():
    name = {name}
    voltage_tier = {voltage_tier}
    inputs = {inputs}
    outputs = {outputs}
    duration = {duration}
    eu_per_gametick = {eu_per_gametick}
            """)

    # Select the appropriate recipe class using the map, default to Standard
    recipe_class = MACHINE_NAME_TO_RECIPE_CLASS.get(name)
    if recipe_class is None:
        recipe_class = StandardOverclockMachineRecipe
        if args.is_verbose():
            print(f"Loaded machine with name '{name}', which is not a registered machine name.")

    if args.is_verbose():
            print(f"recipe_class = {recipe_class}")

    recipe = None
    if recipe_class is StandardOverclockMachineRecipe:
        recipe = recipe_class(name, voltage_tier, inputs, outputs, duration, eu_per_gametick)
    elif recipe_class is PerfectOverclockMachineRecipe:
        recipe = recipe_class(name, voltage_tier, inputs, outputs, duration, eu_per_gametick)
    else:
        raise ValueError(f"recipe_class is of unhandled type: {type(recipe_class)}")

    recipe = recipe_class(name, voltage_tier, inputs, outputs, duration, eu_per_gametick)
    return recipe

def get_file_extension(file_path: str):
    return os.path.splitext(file_path)[1][1:].lower()

def load_factory_config(file_path: str) -> Optional[FactoryConfig]:
    # Read config from file
    parsed_input = None
    try:
        ext = get_file_extension(file_path)
        data = {}
        with open(file_path, 'r') as file:
            if ext == 'json':
                data = json.load(file)
            elif ext == 'yaml':
                data = yaml.safe_load(file)
        parsed_input = InputFactoryConfig(**data)
    except (FileNotFoundError, json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing JSON file: {e}")
        return None

    # Convert from pydantic dataclasses to python dataclasses
    recipes: list[MachineRecipe] = []
    for raw_recipe in parsed_input.recipes:
        recipe = initialize_recipe(raw_recipe)
        recipes.append(recipe)

    targets: list[TargetRate] = []
    for item, quantity in parsed_input.targets.items():
        target = make_target(item, quantity)
        targets.append(target)

    return FactoryConfig(recipes, targets)
