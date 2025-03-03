from typing import Dict, Optional
from pydantic.dataclasses import dataclass as pdataclass
import json
from pydantic import ValidationError

from models import FactoryConfig, GameTicks, Recipe, TargetRate, make_itemstack, make_target

@pdataclass
class InputRecipe:
    m: str
    inputs: Dict[str, float]
    outputs: Dict[str, float]
    dur: int
    eut: int

@pdataclass
class InputFactoryConfig:
    recipes: list[InputRecipe]
    targets: Dict[str, float]

def load_factory_config(file_path: str) -> Optional[FactoryConfig]:
    # Read config from file
    parsed_input = None
    try:
        with open(file_path, 'r') as file:
          data = json.load(file)
        parsed_input = InputFactoryConfig(**data)
    except (FileNotFoundError, json.JSONDecodeError, ValidationError) as e:
        print(f"Error parsing JSON file: {e}")
        return None

    # Convert from pydantic dataclasses to python dataclasses
    recipes: list[Recipe] = []
    for raw_recipe in parsed_input.recipes:
        # TODO: Inputs and Outputs should be floats, not ints. This is to accommodate chance outputs
        name = raw_recipe.m
        inputs = [make_itemstack(item, int(quantity)) for (item, quantity) in raw_recipe.inputs.items()]
        outputs = [make_itemstack(item, int(quantity)) for (item, quantity) in raw_recipe.outputs.items()]
        duration = GameTicks(raw_recipe.dur)
        eu_per_gametick = raw_recipe.eut
        recipe = Recipe(name, inputs, outputs, duration, eu_per_gametick)
        recipes.append(recipe)
    
    targets: list[TargetRate] = []
    for item, quantity in parsed_input.targets.items():
        target = make_target(item, quantity)
        targets.append(target)

    return FactoryConfig(recipes, targets)
