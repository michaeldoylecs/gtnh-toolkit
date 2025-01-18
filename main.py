from collections import defaultdict
from typing import NamedTuple
import pyomo.environ as pyomo

class Recipe(NamedTuple):
    inputs: list[tuple[str, int]]
    outputs: list[tuple[str, int]]
    duration: int

recipe_hydrogen = Recipe(
    inputs = [
        ("water", 500)
    ],
    outputs = [
        ("oxygen", 500),
        ("hydrogen", 1000)
    ],
    duration = 1000,
)

recipe_hydrogen_sulfude = Recipe(
    inputs = [
        ("sulfur", 1),
        ("hydrogen", 2000)
    ],
    outputs = [
        ("hydrogen sulfide", 1000)
    ],
    duration = 60,
)

class Solver():

    def __init__(self, solver = pyomo.SolverFactory('cbc'), model = pyomo.ConcreteModel()):
        self.solver = solver
        self.model = model
        self.currLinkNum = 0
        self.currMachineNum = 0
        self.machineNames = []
        self.sourceLinkMap = defaultdict(list)
        self.sinkLinkMap = defaultdict(list)

        self.model.constraints = pyomo.ConstraintList()


    def solve(self):
        # TODO: Add sanity checks (is target set, is objective set, etc)

        # Add source -> link constraints
        for source, links in self.sourceLinkMap.items():
            self.model.constraints.add(getattr(self.model, source) == -1 * sum(getattr(self.model, link) for link in links))
        
        # Add Link -> Sink constraints
        for sink, links in self.sinkLinkMap.items():
            self.model.constraints.add(getattr(self.model, sink) == sum(getattr(self.model, link) for link in links))

        # Target
        self.model.constraints.add(self.model.M1 >= 1000)

        # Objective
        self.model.objective = pyomo.Objective(
            rule = lambda model: sum([getattr(model, machine_name) for machine_name in self.machineNames]),
            sense = pyomo.minimize,
        )

        # Result
        result = self.solver.solve(self.model)
        print(result)


    def add_recipe(self, recipe: Recipe) -> int:
        # Add machine variable
        machine_name = f"M{self.currMachineNum}"
        setattr(self.model, machine_name, pyomo.Var(domain=pyomo.NonNegativeReals))
        self.currMachineNum += 1
        self.machineNames.append(machine_name)

        # Add variables and constraints for each input
        for input_name, input_quantity in recipe.inputs:
            # Add source if it does not exist yet
            source_name = f"I_{input_name}"
            if not hasattr(self.model, source_name):
                setattr(self.model, source_name, pyomo.Var(domain=pyomo.Reals))

            # Name the link variables
            link_in = f"L{self.currLinkNum}_IN_{input_name}"
            link_out = f"L{self.currLinkNum}_OUT_{input_name}"
            self.currLinkNum += 1

            # Add the link variables
            setattr(self.model, link_in, pyomo.Var(domain=pyomo.NonNegativeReals))
            setattr(self.model, link_out, pyomo.Var(domain=pyomo.NonNegativeReals))

            # Add the link constraints
            # ## What goes in must come out
            self.model.constraints.add(-1 * getattr(self.model, link_in) + getattr(self.model, link_out) == 0)

            # Relate all links to their source
            self.sourceLinkMap[source_name].append(link_in)

            # Add machine constraints for inputs
            ## The items coming from a link must match the number of machines * the recipe quantity.
            self.model.constraints.add(getattr(self.model, machine_name) * input_quantity - getattr(self.model, link_out) == 0)

        # Add variables and constraints for each output
        for output_name, output_quantity in recipe.outputs:
            # Add sink if it does not exist yet
            sink_name = f"O_{output_name}"
            if not hasattr(self.model, sink_name):
                setattr(self.model, sink_name, pyomo.Var(domain=pyomo.Reals))

            # Name the link variables
            link_in = f"L{self.currLinkNum}_IN_{output_name}"
            link_out = f"L{self.currLinkNum}_OUT_{output_name}"
            self.currLinkNum += 1

            # Add the link variables
            setattr(self.model, link_in, pyomo.Var(domain=pyomo.NonNegativeReals))
            setattr(self.model, link_out, pyomo.Var(domain=pyomo.NonNegativeReals))

            # Add the link constraints
            ## What goes in must come out
            self.model.constraints.add(-1 * getattr(self.model, link_in) + getattr(self.model, link_out) == 0)

            # Relate all links to their sink
            self.sinkLinkMap[source_name].append(link_in)

            # Add machine constraints for inputs
            ## The items going out into a link must match the number of machines * the recipe quantity.
            self.model.constraints.add(getattr(self.model, machine_name) * output_quantity - getattr(self.model, link_out) == 0)


def main():
    solver = Solver()
    solver.add_recipe(recipe_hydrogen)
    solver.add_recipe(recipe_hydrogen_sulfude)
    solver.solve()

if __name__ == "__main__":
    main()
