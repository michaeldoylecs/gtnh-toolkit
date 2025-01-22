import abc
from collections import defaultdict
from dataclasses import dataclass, field
import math
import re
from typing import Any
import graphviz # type: ignore
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
        model.SOURCE_CONSTRAINTS.add(source_variable + source_out_variable == 0)

        # Source values must be less than or equal to 0
        model.SOURCE_CONSTRAINTS.add(source_variable <= 0)

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
        rule = lambda model: sum([getattr(model, machine) for machine in machines]) - sum([getattr(model, source) for source in sources]),
        sense = pyomo.minimize,
    )

    # Solve
    result = solver.solve(model)
    return model, result

@dataclass
class Item:
    id: ItemName

@dataclass
class ItemRate:
    item: Item
    quantity: float

class Node:
    __metaclass__ = abc.ABCMeta
    id: str
    data: dict[str, tuple[type, Any]]

    def __init__(self, id: str, **kwargs):
        self.id = id
        self.data = {}
        for key, value in kwargs.items():
            self.data[key] = (type(value), value)

    @abc.abstractmethod
    def type(self) -> str:
        raise NotImplementedError()

class SourceNode(Node):
    def type(self) -> str:
        return 'source'

class SinkNode(Node):
    def type(self) -> str:
        return 'sink'

class MachineNode(Node):
    def type(self) -> str:
        return 'machine'
    
class ItemNode(Node):
    def type(self) -> str:
        return 'item'

@dataclass
class DirectedEdge:
    start: Node
    end: Node
    item: Item
    quantity: float

@dataclass
class SolutionGraph:
    nodes: list[Node] = field(default_factory=list)
    edges: list[DirectedEdge] = field(default_factory=list)

def build_solution_graph(model: pyomo.Model) -> SolutionGraph:
    graph = SolutionGraph()

    # Extract variable names and values
    variables = {str(v): varobject.value for v in model.component_objects(pyomo.Var, active=True) for varobject in [getattr(model, str(v))]}
    
    # Define regex patterns
    machine_pattern = re.compile(r'^(M\d+)$')
    machine_input_pattern = re.compile(r'^(M\d+)_IN_((?:(?!TO_).)+)$')
    machine_output_pattern = re.compile(r'^(M\d+)_OUT_((?:(?!TO_).)+)$')
    sink_pattern = re.compile(r'^SINK_((?:(?!IN_).)+)$')
    sink_in_pattern = re.compile(r'^SINK_IN_.*$')
    source_pattern = re.compile(r'^SOURCE_(?:(?!OUT_))((?:(?!TO_).)+)$')
    source_out_pattern = re.compile(r'^SOURCE_OUT_(?:(?!TO_).)+$')
    link_pattern = re.compile(r'^(.*)_TO_(.*)$')
    
    # Filter variables by patterns
    machines = {k: v for k, v in variables.items() if machine_pattern.match(k)}
    sources = {k: v for k, v in variables.items() if source_pattern.match(k)}
    source_outs = {k: v for k, v in variables.items() if source_out_pattern.match(k)}
    sinks = {k: v for k, v in variables.items() if sink_pattern.match(k)}
    sink_ins = {k: v for k, v in variables.items() if sink_in_pattern.match(k)}
    links = [{"start": s, "end": e, "value": v} for k, v in variables.items() if (match := link_pattern.match(k)) for s, e in [match.groups()]]

    # Associate machines and their inputs
    machine_inputs: list[tuple[str, str, float]] = []
    for k, v in variables.items():
        match = machine_input_pattern.match(k)
        if match:
            machine, *_ = match.groups()
            machine_inputs.append((machine, k, v))
    
    # Associate machines and their outputs
    machine_outputs: list[tuple[str, str, float]] = []
    for k, v in variables.items():
        match = machine_output_pattern.match(k)
        if match:
            machine, *_ = match.groups()
            machine_outputs.append((machine, k, v))

    # Print filtered variables
    print("\nMachines:")
    for k, v in machines.items():
        print(f"{k} = {v}")

    print("\nMachine inputs:")
    for m, k, v in machine_inputs:
        print(f"{m}: {k} = {v}")
    
    print("\nMachine outputs:")
    for m, k, v in machine_outputs:
        print(f"{m}: {k} = {v}")
    
    print("\nSources:")
    for k, v in sources.items():
        print(f"{k} = {v}")
    
    print("\nSource OUTs:")
    for k, v in source_outs.items():
        print(f"{k} = {v}")

    print("\nSinks:")
    for k, v in sinks.items():
        print(f"{k} = {v}")
    
    print("\nSink INs:")
    for k, v in sink_ins.items():
        print(f"{k} = {v}")
    
    print("\nLinks:")
    for link in links:
        print(link)

    # Map to relate the string name of a link within a link to its corresponding node.
    link_name_to_node_map: dict[str, Node] = {}

    # Make source nodes
    source_nodes: dict[str, SourceNode] = {}
    for source, quantity in sources.items():
        if math.isclose(quantity, 0.0):
            continue

        match = source_pattern.match(source)
        if match:
            source_name, = match.groups()
            source_node = SourceNode(id = source, **{
                'item': Item(id = ItemName(source_name)),
                'rate': quantity,
            })
            source_nodes[source_name] = source_node
            link_name_to_node_map[source] = source_node
            graph.nodes.append(source_node)

    # Make source OUT nodes
    for source_out, quantity in source_outs.items():
        if math.isclose(quantity, 0.0):
            continue

        source_out_node = ItemNode(id = source_out, )
        link_name_to_node_map[source_out] = source_out_node
        graph.nodes.append(source_out_node)

        # Create edge between source node and source OUT node
        source = str.replace(source_out, '_OUT', '')
        item_name = str.replace(source_out, 'SOURCE_OUT_', '')
        graph.edges.append(DirectedEdge(
            start = link_name_to_node_map[source],
            end = link_name_to_node_map[source_out],
            item = Item(id = ItemName(item_name)),
            quantity = quantity,
        ))

    # Make sink nodes
    sink_nodes: dict[str, SinkNode] = {}
    for sink, quantity in sinks.items():
        if math.isclose(quantity, 0.0):
            continue

        match = sink_pattern.match(sink)
        if match:
            sink_name, = match.groups()
            sink_node = SinkNode(id = sink, **{
                'item': Item(id = ItemName(sink_name)),
                'rate': quantity,
            })
            sink_nodes[sink_name] = sink_node
            link_name_to_node_map[sink] = sink_node
            graph.nodes.append(sink_node)

    # Make sink IN nodes
    for sink_in, quantity in sink_ins.items():
        if math.isclose(quantity, 0.0):
            continue

        sink_in_node = ItemNode(id = sink_in)
        link_name_to_node_map[sink_in] = sink_in_node
        graph.nodes.append(sink_in_node)

        # Create edge between sink IN node and sink node
        sink = str.replace(sink_in, '_IN', '')
        item_name = str.replace(sink_in, 'SINK_IN_', '')
        graph.edges.append(DirectedEdge(
            start = link_name_to_node_map[sink_in],
            end = link_name_to_node_map[sink],
            item = Item(id = ItemName(item_name)),
            quantity = quantity,
        ))
    
    # Make machine nodes
    machine_nodes: dict[str, MachineNode] = {}
    for machine, quantity in machines.items():
        match = machine_pattern.match(machine)
        if match:
            machine_name, = match.groups()
            machine_node = MachineNode(id = machine, **{
                'item': Item(id = ItemName(machine_name)),
                'quantity': quantity,
            })
            machine_nodes[machine_name] = machine_node
            link_name_to_node_map[machine] = machine_node
            graph.nodes.append(machine_node)

    # Make machine IN nodes
    for machine, input_node_name, quantity in machine_inputs:
        if math.isclose(quantity, 0.0):
            continue

        match = machine_input_pattern.match(input_node_name)
        if match:
            _, item_name = match.groups()
            input_node = ItemNode(id = input_node_name, **{
                'item': Item(id = ItemName(item_name)),
                'quantity': quantity,
            })
            link_name_to_node_map[input_node_name] = input_node
            graph.nodes.append(input_node)

            # Create edge between machine and machine input node
            graph.edges.append(DirectedEdge(
                start = link_name_to_node_map[input_node_name],
                end = link_name_to_node_map[machine],
                item = Item(id = ItemName(item_name)),
                quantity = quantity,
            ))

    # Make machine OUT nodes
    for machine, output_node_name, quantity in machine_outputs:
        if math.isclose(quantity, 0.0):
            continue

        match = machine_output_pattern.match(output_node_name)
        if match:
            _, item_name, = match.groups()
            output_node = ItemNode(id = output_node_name, **{
                'item': Item(id = ItemName(item_name)),
                'quantity': quantity,
            })
            link_name_to_node_map[output_node_name] = output_node
            graph.nodes.append(output_node)

            # Create edge between machine and machine output node
            graph.edges.append(DirectedEdge(
                start = link_name_to_node_map[machine],
                end = link_name_to_node_map[output_node_name],
                item = Item(id = ItemName(item_name)),
                quantity = quantity,
            ))

    # Make edges
    for link in links:
        value = link["value"]
        if math.isclose(value, 0.0):
            continue

        start = link_name_to_node_map[link["start"]]
        end = link_name_to_node_map[link["end"]]

        graph.edges.append(DirectedEdge(
            start = start,
            end = end,
            item = end.data['item'][1],
            quantity = value
        ))

    return graph


def draw(graph: SolutionGraph):
    # Make the graph
    dot = graphviz.Digraph(comment='GTNH-ToolKit')

    # Style the graph
    dot.attr(rankdir='TB')

    # Add the nodes
    for node in graph.nodes:
        if node.type() == 'source':
            with dot.subgraph(name='cluster_sources') as subgraph:
                subgraph.attr(rank='source', color='lightgrey', style='filled')
                subgraph.node(node.id, f'{node.data['item'][1].id}\n{node.data['rate'][1]}')

        if node.type() == 'sink':
            with dot.subgraph(name='cluster_sinks') as subgraph:
                subgraph.attr(rank="sink", color='lightgrey', style='filled')
                subgraph.node(node.id, f'{node.data['item'][1].id}\n{node.data['rate'][1]}')
        
        if node.type() == 'machine':
            with dot.subgraph(name='regular') as subgraph:
                dot.node(node.id, f'{node.id}={node.data['quantity'][1]}')

        if node.type() == 'item':
            with dot.subgraph(name='regular') as subgraph:
                subgraph.node(node.id, node.id, **{
                    'width': '0',
                    'height': '0',
                })

    # Add the edges
    for edge in graph.edges:
        dot.edge(edge.start.id, edge.end.id, label = f'({edge.quantity})')

    dot.render('./output/test.gv', format='png').replace('\\', '/')

    
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

    # draw(model)

    graph = build_solution_graph(model)
    print(graph.nodes)
    print(graph.edges)

    draw(graph)

if __name__ == "__main__":
    main()
