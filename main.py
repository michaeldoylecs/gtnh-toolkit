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
        self.itemInLinks = defaultdict(list)
        self.itemOutLinks = defaultdict(list)
        self.sourceLinkMap = defaultdict(list)
        self.sinkLinkMap = defaultdict(list)

        self.model.constraints = pyomo.ConstraintList()


    def solve(self):
        # TODO: Add sanity checks (is target set, is objective set, etc)

        # Add source -> link constraints
        for source, links in self.sourceLinkMap.items():
            # Sources must be negative or 0.
            self.model.constraints.add(getattr(self.model, source) <= 0)
            # Sources must equal the sum of their outgoing links.
            self.model.constraints.add(getattr(self.model, source) + sum(getattr(self.model, link) for link in links) == 0)
        
        # Add Link -> Sink constraints
        ## Sinks must be positive or 0
        for sink, _ in self.sinkLinkMap.items():
            self.model.constraints.add(getattr(self.model, sink) >= 0)
        ## Any excess Link OUT that is not consumed by a Link IN must go to a Sink
        ## Sink = sum(sink_in_links) - sum(source_out_links)
        for item, out_links in self.itemOutLinks.items():
            sink = f"O_{item}"
            source = f"I_{item}"
            if hasattr(self.model, sink):
                self.model.constraints.add(getattr(self.model, sink) == sum(getattr(self.model, sink_link) for sink_link in self.sinkLinkMap[sink]) - sum(getattr(self.model, source_link) for source_link in self.sourceLinkMap[source]))

        # Target
        self.model.constraints.add(getattr(self.model, "O_hydrogen sulfide") >= 1000)

        # Objective
        self.model.objective = pyomo.Objective(
            rule = lambda model: sum([getattr(model, machine_name) for machine_name in self.machineNames]),
            sense = pyomo.minimize,
        )

        # Print all constraints
        self.model.pprint()

        # Result
        result = self.solver.solve(self.model)
        print(result)
        
        # Print the results
        for v in self.model.component_objects(pyomo.Var, active=True):
            varobject = getattr(self.model, str(v))
            for index in varobject:
                print(f"{v} {index} = {varobject[index].value}")


    def add_recipe(self, recipe: Recipe) -> int:
        # Add machine variable
        machine_name = f"M{self.currMachineNum}"
        setattr(self.model, machine_name, pyomo.Var(domain=pyomo.NonNegativeReals))
        self.model.constraints.add(getattr(self.model, machine_name) >= 0)
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
            self.itemInLinks[input_name].append(link_in)
            self.itemOutLinks[input_name].append(link_out)

            # Add machine constraints for inputs
            ## The items coming from a link must match the number of machines * the recipe quantity.
            self.model.constraints.add(getattr(self.model, machine_name) * input_quantity - getattr(self.model, link_out) == 0)

        # Add variables and constraints for each output
        for output_name, output_quantity in recipe.outputs:
            # Add sink if it does not exist yet
            sink_name = f"O_{output_name}"
            if not hasattr(self.model, sink_name):
                setattr(self.model, sink_name, pyomo.Var(domain=pyomo.NonNegativeReals))

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
            self.sinkLinkMap[sink_name].append(link_in)
            self.itemInLinks[output_name].append(link_in)
            self.itemOutLinks[output_name].append(link_out)

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
