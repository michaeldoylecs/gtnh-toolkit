from collections import defaultdict
from dataclasses import dataclass
import pyomo.environ as pyomo # type: ignore
from pyomo.opt import SolverResults # type: ignore


class ItemName(str):
    def __new__(cls, value):
        # ItemNames must not contain spaces. Spaces must be replaced with underscores.
        value = value.replace(" ", "_")
        return str.__new__(cls, value)

@dataclass
class Recipe:
    inputs: list[tuple[ItemName, int]]
    outputs: list[tuple[ItemName, int]]
    duration: int

@dataclass
class TargetRate:
    item: ItemName
    quantity: float

def solve(
        recipes: list[Recipe],
        target: TargetRate,
        solver = pyomo.SolverFactory('cbc'),
        model = pyomo.ConcreteModel()
        ) -> tuple[pyomo.Model, SolverResults]:
    machine_index = 0
    machines: list[str] = [] 

    item_out_links: dict[ItemName, list[str]] = defaultdict(list)
    item_in_links: dict[ItemName, list[str]] = defaultdict(list)

    for recipe in recipes:
        machine_name = f'M{machine_index}'
        machine_index += 1
        machines.append(machine_name)

        # Make machine variable and empty constraint list
        setattr(model, machine_name, pyomo.Var(domain=pyomo.NonNegativeReals))
        setattr(model, f'{machine_name}_constraints', pyomo.ConstraintList())
        machine_variable = getattr(model, machine_name)

        # Make input variables and constraints
        for item, quantity in recipe.inputs:
            item_in_link = f'{machine_name}_IN_{item}'
            setattr(model, item_in_link, pyomo.Var(domain=pyomo.NonNegativeReals))
            item_in_links[item].append(item_in_link)
            input_variable = getattr(model, item_in_link)
            getattr(model, f'{machine_name}_constraints').add(machine_variable == input_variable / quantity)

        # Make output variables and constraints
        for item, quantity in recipe.outputs:
            item_out_link = f'{machine_name}_OUT_{item}'
            setattr(model, item_out_link, pyomo.Var(domain=pyomo.NonNegativeReals))
            item_out_links[item].append(item_out_link)
            output_variable = getattr(model, item_out_link)
            getattr(model, f'{machine_name}_constraints').add(machine_variable == output_variable / quantity)

        # Add recipe constraints between inputs, outputs
        input_output_pairs = [(i, o) for i in recipe.inputs for o in recipe.outputs]
        for (in_item, in_quantity), (out_item, out_quantity) in input_output_pairs:
            in_variable = getattr(model, f'{machine_name}_IN_{in_item}')
            out_variable = getattr(model, f'{machine_name}_OUT_{out_item}')
            getattr(model, f'{machine_name}_constraints').add((out_variable / out_quantity) - (in_variable / in_quantity) == 0)
    
    # Make sources for each IN link item
    item_source_map: dict[ItemName, str] = dict()
    model.SOURCE_CONSTRAINTS = pyomo.ConstraintList()
    for item in item_in_links.keys():
        source_name = f'SOURCE_{item}'
        source_out_name = f'SOURCE_OUT_{item}'
        setattr(model, source_name, pyomo.Var(domain=pyomo.Reals))
        setattr(model, source_out_name, pyomo.Var(domain=pyomo.NonNegativeReals))

        # Source value should be the negative of its outgoing quantity
        source_variable = getattr(model, source_name)
        source_out_variable = getattr(model, source_out_name)
        model.SOURCE_CONSTRAINTS.add(source_variable - source_out_variable == 0)

        # Source values must be less than or equal to 0
        model.SOURCE_CONSTRAINTS.add(source_variable >= 0)

        item_source_map[item] = source_name
        item_out_links[item].append(source_out_name)

    # Make sinks for each OUT link item
    item_sink_map: dict[ItemName, str] = dict()
    model.SINK_CONSTRAINTS = pyomo.ConstraintList()
    for item in item_out_links.keys():
        sink_name = f'SINK_{item}'
        sink_in_name = f'SINK_IN_{item}'
        setattr(model, sink_name, pyomo.Var(domain=pyomo.NonNegativeReals))
        setattr(model, sink_in_name, pyomo.Var(domain=pyomo.NonNegativeReals))

        # Sink value should be equal to its incoming quantity
        sink_variable = getattr(model, sink_name)
        sink_in_variable = getattr(model, sink_in_name)
        model.SINK_CONSTRAINTS.add(sink_variable == sink_in_variable)

        # Sink values must be greater than or equal to 0
        model.SINK_CONSTRAINTS.add(sink_variable >= 0)

        item_sink_map[item] = sink_name
        item_in_links[item].append(sink_name)
    
    # Add links between all OUTs and INs of the same item
    incoming_link_map: dict[str, list[str]] = defaultdict(list)
    outgoing_link_map: dict[str, list[str]] = defaultdict(list)
    for item in item_out_links.keys():
        output_input_pairs = [(o, i) for i in item_in_links[item] for o in item_out_links[item]]
        for out_link, in_link in output_input_pairs:
            link_name = f'{out_link}_TO_{in_link}'
            setattr(model, link_name, pyomo.Var(domain=pyomo.NonNegativeReals))
            incoming_link_map[in_link].append(link_name)
            outgoing_link_map[out_link].append(link_name)

            out_variable = getattr(model, out_link)
            in_variable = getattr(model, in_link)
    
    # In links must sum to their connecting edges
    model.IN_LINK_EDGE_CONSTRAINTS = pyomo.ConstraintList()
    for in_link, incoming_edges in incoming_link_map.items():
        model.IN_LINK_EDGE_CONSTRAINTS.add(getattr(model, in_link) == sum([getattr(model, edge) for edge in incoming_edges]))

    # Out links must sum to their connecting edges
    model.OUT_LINK_EDGE_CONSTRAINTS = pyomo.ConstraintList()
    for out_link, outgoing_edges in outgoing_link_map.items():
        model.OUT_LINK_EDGE_CONSTRAINTS.add(getattr(model, out_link) == sum([getattr(model, edge) for edge in outgoing_edges]))

    # Add target
    model.target = pyomo.Constraint(rule=lambda model: getattr(model, f'SINK_{target.item}') >= target.quantity)

    # Add objective
    sources = item_source_map.values()
    model.objective = pyomo.Objective(
        rule = lambda model: sum([getattr(model, machine) for machine in machines]) + sum([getattr(model, source) for source in sources]),
        sense = pyomo.minimize,
    )

    # Solve
    result = solver.solve(model)
    return model, result

def main():
    # Dummy data
    recipe_hydrogen = Recipe(
        inputs = [
            (ItemName("water"), 500)
        ],
        outputs = [
            (ItemName("oxygen"), 500),
            (ItemName("hydrogen"), 1000)
        ],
        duration = 1000,
    )
    recipe_hydrogen_sulfude = Recipe(
        inputs = [
            (ItemName("sulfur"), 1),
            (ItemName("hydrogen"), 2000)
        ],
        outputs = [
            (ItemName("hydrogen sulfide"), 1000)
        ],
        duration = 60,
    )

    target: TargetRate = TargetRate(
        item = ItemName("hydrogen sulfide"),
        quantity = 5000,
    )

    model, results = solve([recipe_hydrogen, recipe_hydrogen_sulfude], target)

    # Print the results
    model.pprint()
    print(results)
    for v in model.component_objects(pyomo.Var, active=True):
        varobject = getattr(model, str(v))
        print(f"{v} = {varobject.value}")

if __name__ == "__main__":
    main()
