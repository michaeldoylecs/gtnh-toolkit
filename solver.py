from collections import defaultdict
import pyomo.environ as pyomo # type: ignore
from pyomo.opt import SolverResults # type: ignore
from gamelogic.Machines import MachineRecipe
from models import Item, TargetRate

def solve(
        recipes: list[MachineRecipe],
        target: TargetRate,
        solver = pyomo.SolverFactory('cbc'),
        model = pyomo.ConcreteModel()
        ) -> tuple[pyomo.Model, SolverResults, dict[str, MachineRecipe]]:
    machine_index = 0
    machines: list[str] = [] 
    machine_id_to_recipe_map: dict[str, MachineRecipe] = {}
    machine_outputs: set[Item] = set()

    item_out_links: dict[Item, list[str]] = defaultdict(list)
    item_in_links: dict[Item, list[str]] = defaultdict(list)

    for recipe in recipes:
        machine_name = f'M{machine_index}'
        machine_index += 1
        machines.append(machine_name)
        machine_id_to_recipe_map[machine_name] = recipe

        # Make machine variable and empty constraint list
        setattr(model, machine_name, pyomo.Var(domain=pyomo.NonNegativeReals))
        setattr(model, f'{machine_name}_constraints', pyomo.ConstraintList())
        machine_variable = getattr(model, machine_name)

        # Make input variables and constraints
        for itemstack in recipe.inputs:
            item_in_link = f'{machine_name}_IN_{itemstack.item.name}'
            setattr(model, item_in_link, pyomo.Var(domain=pyomo.NonNegativeReals))
            item_in_links[itemstack.item].append(item_in_link)
            input_variable = getattr(model, item_in_link)
            # Update rate calculation:
            rate = itemstack.quantity / recipe.duration.as_seconds()
            getattr(model, f'{machine_name}_constraints').add(machine_variable == input_variable / rate)

        # Make output variables and constraints
        for itemstack in recipe.outputs:
            machine_outputs.add(itemstack.item)
            item_out_link = f'{machine_name}_OUT_{itemstack.item.name}'
            setattr(model, item_out_link, pyomo.Var(domain=pyomo.NonNegativeReals))
            item_out_links[itemstack.item].append(item_out_link)
            output_variable = getattr(model, item_out_link)
            # Update rate calculation:
            rate = itemstack.quantity / recipe.duration.as_seconds()
            getattr(model, f'{machine_name}_constraints').add(machine_variable == output_variable / rate)

        # Add recipe constraints between inputs, outputs
        input_output_pairs = [(i, o) for i in recipe.inputs for o in recipe.outputs]
        for in_itemstack, out_itemstack in input_output_pairs:
            in_variable = getattr(model, f'{machine_name}_IN_{in_itemstack.item.name}')
            out_variable = getattr(model, f'{machine_name}_OUT_{out_itemstack.item.name}')
            # Update rate calculations:
            in_rate = in_itemstack.quantity / recipe.duration.as_seconds()
            out_rate = out_itemstack.quantity / recipe.duration.as_seconds()
            getattr(model, f'{machine_name}_constraints').add((out_variable / out_rate) - (in_variable / in_rate) == 0)
    
    # Make sources for each IN link item
    item_source_map: dict[Item, str] = dict()
    model.SOURCE_CONSTRAINTS = pyomo.ConstraintList()
    for item in item_in_links.keys():
        source_name = f'SOURCE_{item.name}'
        source_out_name = f'SOURCE_OUT_{item.name}'
        setattr(model, source_name, pyomo.Var(domain=pyomo.Reals))
        setattr(model, source_out_name, pyomo.Var(domain=pyomo.NonNegativeReals))

        # Source value should be the negative of its outgoing quantity
        source_variable = getattr(model, source_name)
        source_out_variable = getattr(model, source_out_name)
        model.SOURCE_CONSTRAINTS.add(source_variable + source_out_variable == 0)

        # Source values must be less than or equal to 0
        model.SOURCE_CONSTRAINTS.add(source_variable <= 0)

        item_source_map[item] = source_name
        item_out_links[item].append(source_out_name)

    # Make sinks for each OUT link item
    item_sink_map: dict[Item, str] = dict()
    model.SINK_CONSTRAINTS = pyomo.ConstraintList()
    for item in item_out_links.keys():
        sink_name = f'SINK_{item.name}'
        sink_in_name = f'SINK_IN_{item.name}'
        setattr(model, sink_name, pyomo.Var(domain=pyomo.NonNegativeReals))
        setattr(model, sink_in_name, pyomo.Var(domain=pyomo.NonNegativeReals))

        # Sink value should be equal to its incoming quantity
        sink_variable = getattr(model, sink_name)
        sink_in_variable = getattr(model, sink_in_name)
        model.SINK_CONSTRAINTS.add(sink_variable == sink_in_variable)

        # Sink values must be greater than or equal to 0
        model.SINK_CONSTRAINTS.add(sink_variable >= 0)

        item_sink_map[item] = sink_name
        item_in_links[item].append(sink_in_name)
    
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
    
    # In links must sum to their connecting edges
    model.IN_LINK_EDGE_CONSTRAINTS = pyomo.ConstraintList()
    for in_link, incoming_edges in incoming_link_map.items():
        model.IN_LINK_EDGE_CONSTRAINTS.add(getattr(model, in_link) == sum([getattr(model, edge) for edge in incoming_edges]))

    # Out links must sum to their connecting edges
    model.OUT_LINK_EDGE_CONSTRAINTS = pyomo.ConstraintList()
    for out_link, outgoing_edges in outgoing_link_map.items():
        model.OUT_LINK_EDGE_CONSTRAINTS.add(getattr(model, out_link) == sum([getattr(model, edge) for edge in outgoing_edges]))

    # Add target
    model.target = pyomo.Constraint(rule=lambda model: getattr(model, f'SINK_{target.item.name}') >= target.quantity_per_second)

    # Add taxes on sources which are a machine output
    taxes: list[str] = []
    model.SOURCE_TAX_CONSTRAINTS = pyomo.ConstraintList()
    for item, source_name in item_source_map.items():
        if item in machine_outputs:
            source_tax_name = f'SOURCE_TAX_{item.name}'
            setattr(model, source_tax_name, pyomo.Var(domain=pyomo.NonNegativeReals))
            tax_variable = getattr(model, source_tax_name)
            source_variable = getattr(model, source_name)
            model.SOURCE_TAX_CONSTRAINTS.add(tax_variable == source_variable * -50000)
            taxes.append(source_tax_name)

    # Add objective
    sources = item_source_map.values()
    model.objective = pyomo.Objective(
        # rule = minimize: sum(machines) + sum(source inputs) + sum(tax)
        rule = lambda model:                                            \
            sum([getattr(model, machine) for machine in machines])      \
            + -1 * sum([getattr(model, source) for source in sources])  \
            + sum([getattr(model, tax) for tax in taxes]),
        sense = pyomo.minimize,
    )

    # Solve
    result = solver.solve(model)

    # TODO: Export a more useful object than a pyomo model
    return model, result, machine_id_to_recipe_map
