from typing import NewType
# Need to import VoltageTier for the type hint, and potentially ItemStack if used directly here later.
# Assuming Items.py exists at the same level as Electricity.py
# If gamelogic/Items.py doesn't exist or ItemStack isn't defined there, this import will fail.
# Let's assume it exists for now based on the original BasicMachine.py imports.
try:
    from gamelogic.Items import ItemStack
except ImportError:
    # Define a placeholder if Items module or ItemStack is not found
    # This allows the code to run but might lack full functionality
    # depending on how ItemStack is used.
    print("Warning: gamelogic.Items or ItemStack not found. Using placeholder.")
    class ItemStack: pass # Placeholder definition

from gamelogic.Electricity import VoltageTier

GameTicks = NewType('GameTicks', int)

class MachineRecipe():
    machine_name: str
    machine_tier: VoltageTier # Changed from machine_voltage to machine_tier
    inputs: list[ItemStack]
    outputs: list[ItemStack]
    duration: GameTicks
    eu_per_gametick: int
