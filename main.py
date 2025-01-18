from collections import defaultdict
from typing import TypedDict
import pyomo.environ as pyomo

class Recipe(TypedDict):
    inputs: list[(str, int)]
    outputs: list[(str, int)]
    duration: int

recipe_hydrogen: Recipe = {
    "inputs": [
        ("water", 500)
    ],
    "outputs": [
        ("oxygen", 500),
        ("hydrogen", 1000)
    ],
    "duration": 1000,
}

recipe_hydrogen_sulfude: Recipe = {
    "inputs": [
        ("sulfur", 1),
        ("hydrogen", 2000)
    ],
    "outputs": [
        ("hydrogen sulfide", 1000)
    ],
    "duration": 60,
}

class Solver():

    def __init__(self, solver = pyomo.SolverFactory('cbc'), model = pyomo.ConcreteModel()):
        self.solver = solver
        self.model = model
        self.currLinkNum = 0
        self.currMachineNum = 0
        self.sourceLinkMap = defaultdict(list)
        self.sinkLinkMap = defaultdict(list)


    def solve(self):
        # Add source -> link constraints
        for source, links in self.sourceLinkMap.items():
            self.model.constraints.add(getattr(self.model, source) == -1 * sum(getattr(self.model, link) for link in links))
        
        # Add Link -> Sink constraints
        for sink, links in self.sinkLinkMap.items():
            self.model.constraints.add(getattr(self.model, sink) == sum(getattr(self.model, link) for link in links))

        # Target
        self.model.constraints.add(self.model.a_hydrogen_sulfide >= 1000)

        # Objective
        self.model.objective = pyomo.Objective(
            rule = lambda model: model.a_electrolyzer_hydrogen_recipe + model.a_lcr_hydrogen_sulfide_recipe,
            sense = pyomo.minimize,
        )

        # Result
        result = self.solver.solve(self.model)
        print(result)


    def add_recipe(self, model: pyomo.Model, recipe: Recipe) -> int:
        # Add machine variable
        machine_name = f"M{self.currMachineNum}"
        setattr(model, machine_name, pyomo.Var(domain=pyomo.NonNegativeReals))
        self.currMachineNum += 1

        # Add variables and constraints for each input
        for input_name, input_quantity in self.__get_inputs(recipe):
            # Add source if it does not exist yet
            source_name = f"I_{input_name}"
            if not hasattr(model, source_name):
                setattr(model, source_name, pyomo.Var(domain=pyomo.Reals))

            # Name the link variables
            link_in = f"L{self.currLinkNum}_IN_{input_name}"
            link_out = f"L{self.currLinkNum}_OUT_{input_name}"
            self.currLinkNum += 1

            # Add the link variables
            setattr(model, link_in, pyomo.Var(domain=pyomo.NonNegativeReals))
            setattr(model, link_out, pyomo.Var(domain=pyomo.NonNegativeReals))

            # Add the link constraints
            # ## What goes in must come out
            self.model.constraints.add(-1 * self.model[link_in] + self.model[link_out] == 0)

            # TODO: How do we relate all links to their source?
            self.sourceLinkMap[source_name].append(link_in)

            # Add machine constraints for inputs
            ## The items coming from a link must match the number of machines * the recipe quantity.
            model.constraints.add(model[machine_name] * input_quantity - model[link_out] == 0)

        # Add variables and constraints for each output
        for output_name, output_quantity in self.__get_outputs(recipe):
            # Add sink if it does not exist yet
            sink_name = f"O_{output_name}"
            if not hasattr(model, sink_name):
                setattr(model, sink_name, pyomo.Var(domain=pyomo.Reals))

            # Name the link variables
            link_in = f"L{self.currLinkNum}_IN_{output_name}"
            link_out = f"L{self.currLinkNum}_OUT_{output_name}"
            self.currLinkNum += 1

            # Add the link variables
            setattr(model, link_in, pyomo.Var(domain=pyomo.NonNegativeReals))
            setattr(model, link_out, pyomo.Var(domain=pyomo.NonNegativeReals))

            # Add the link constraints
            ## What goes in must come out
            model.constraints.add(-1 * model[link_in] + model[link_out] == 0)

            # TODO: How do we relate all links to their sink?
            self.sinkLinkMap[source_name].append(link_in)

            # Add machine constraints for inputs
            ## The items going out into a link must match the number of machines * the recipe quantity.
            model.constraints.add(model[machine_name] * output_quantity - model[link_out] == 0)



    def __get_inputs(self, recipe: Recipe) -> list[str]:
        return [input_name for input_name, _ in recipe["inputs"]]

    def __get_outputs(self, recipe: Recipe) -> list[str]:
        return [input_name for input_name, _ in recipe["outputs"]]

    def __get_inputs_from_list(self, recipes: list[Recipe]) -> list[str]:
        inputs = set()
        for recipe in recipes:
            inputs.update(self.__get_inputs(recipe))
        return list(inputs)

    def __get_outputs_from_list(self, recipes: list[Recipe]) -> list[str]:
        outputs = set()
        for recipe in recipes:
            outputs.update(self.__get_inputs(recipe))
        return list(outputs)

def main():
    solver = Solver()
    solver.add_recipe(recipe_hydrogen)
    solver.add_recipe(recipe_hydrogen_sulfude)
    solver.solve()

if __name__ == "__main__":
    main()
