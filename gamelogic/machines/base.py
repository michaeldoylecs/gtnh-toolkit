from abc import ABC, abstractmethod
from gamelogic.items import ItemStack
from gamelogic.electricity import Voltage, VoltageTier
from gamelogic.game_time import GameTime

class MachineRecipe(ABC):

    @property
    @abstractmethod
    def machine_name(self) -> str:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def machine_tier(self) -> VoltageTier:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def inputs(self) -> list[ItemStack]:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def outputs(self) -> list[ItemStack]:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def duration(self) -> GameTime:
        raise NotImplementedError
    
    @property
    @abstractmethod
    def eu_per_gametick(self) -> Voltage:
        raise NotImplementedError
