import abc
from collections import defaultdict
from dataclasses import dataclass, field
import math
import re
import graphviz # type: ignore
import pyomo.environ as pyomo # type: ignore

from models import Item, make_item


@dataclass
class ItemRate:
    item: Item
    quantity: float

class Node:
    __metaclass__ = abc.ABCMeta
    id: str

    def __init__(self, id: str):
        self.id = id

class SourceNode(Node):
    item: str
    quantity: float

    def __init__(self, id: str, item: str, quantity: float):
        self.item = item
        self.quantity = quantity
        super().__init__(id)

class SinkNode(Node):
    item: str
    quantity: float

    def __init__(self, id: str, item: str, quantity: float):
        self.item = item
        self.quantity = quantity
        super().__init__(id)

class MachineNode(Node):
    machine_name: str
    quantity: float

    def __init__(self, id: str, machine_name: str, quantity: float):
        self.machine_name = machine_name
        self.quantity = quantity
        super().__init__(id)

class MachineInputNode(Node):
    machine_id: str
    item: str
    quantity: float

    def __init__(self, id: str, machine_id: str, item: str, quantity: float):
        self.machine_id = machine_id
        self.item = item
        self.quantity = quantity
        super().__init__(id)

class MachineOutputNode(Node):
    machine_id: str
    item: str
    quantity: float

    def __init__(self, id: str, machine_id: str, item: str, quantity: float):
        self.machine_id = machine_id
        self.item = item
        self.quantity = quantity
        super().__init__(id)
    
class ItemNode(Node):
    item: str
    quantity: float

    def __init__(self, id: str, item: str, quantity: float):
        self.item = item
        self.quantity = quantity
        super().__init__(id)

@dataclass
class DirectedEdge:
    start: Node
    end: Node

@dataclass
class ItemDirectedEdge(DirectedEdge):
    item: Item
    quantity: float

@dataclass
class MachineInputDirectedEdge(DirectedEdge):
    '''Edge subclass to differentiate machine input edges'''
    machine_id: str

@dataclass
class MachineOutputDirectedEdge(DirectedEdge):
    '''Edge subclass to differentiate machine output edges'''
    machine_id: str

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
            source_node = SourceNode(id = source, item = source_name, quantity = quantity)
            source_nodes[source_name] = source_node
            link_name_to_node_map[source] = source_node
            graph.nodes.append(source_node)

    # Make source OUT nodes
    for source_out, quantity in source_outs.items():
        if math.isclose(quantity, 0.0):
            continue

        item_name = str.replace(source_out, 'SOURCE_OUT_', '')
        source_out_node = ItemNode(id = source_out, item = item_name, quantity = quantity)
        link_name_to_node_map[source_out] = source_out_node
        graph.nodes.append(source_out_node)

        # Create edge between source node and source OUT node
        source = str.replace(source_out, '_OUT', '')
        graph.edges.append(ItemDirectedEdge(
            start = link_name_to_node_map[source],
            end = link_name_to_node_map[source_out],
            item = make_item(item_name),
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
            sink_node = SinkNode(id = sink, item = sink_name, quantity = quantity)
            sink_nodes[sink_name] = sink_node
            link_name_to_node_map[sink] = sink_node
            graph.nodes.append(sink_node)

    # Make sink IN nodes
    for sink_in, quantity in sink_ins.items():
        if math.isclose(quantity, 0.0):
            continue

        item_name = str.replace(sink_in, 'SINK_IN_', '')
        sink_in_node = ItemNode(id = sink_in, item = item_name, quantity = quantity)
        link_name_to_node_map[sink_in] = sink_in_node
        graph.nodes.append(sink_in_node)

        # Create edge between sink IN node and sink node
        sink = str.replace(sink_in, '_IN', '')
        graph.edges.append(ItemDirectedEdge(
            start = link_name_to_node_map[sink_in],
            end = link_name_to_node_map[sink],
            item = make_item(item_name),
            quantity = quantity,
        ))
    
    # Make machine nodes
    machine_nodes: dict[str, MachineNode] = {}
    for machine, quantity in machines.items():
        match = machine_pattern.match(machine)
        if match:
            machine_name, = match.groups()
            machine_node = MachineNode(id = machine, machine_name = machine_name, quantity = quantity)
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
            input_node = MachineInputNode(id = input_node_name, machine_id = machine, item = item_name, quantity = quantity)
            link_name_to_node_map[input_node_name] = input_node
            graph.nodes.append(input_node)

            # Create edge between machine and machine input node
            graph.edges.append(MachineInputDirectedEdge(
                start = link_name_to_node_map[input_node_name],
                end = link_name_to_node_map[machine],
                machine_id = machine,
            ))

    # Make machine OUT nodes
    for machine, output_node_name, quantity in machine_outputs:
        if math.isclose(quantity, 0.0):
            continue

        match = machine_output_pattern.match(output_node_name)
        if match:
            _, item_name, = match.groups()
            output_node = MachineOutputNode(id = output_node_name, machine_id = machine,  item = item_name, quantity = quantity)
            link_name_to_node_map[output_node_name] = output_node
            graph.nodes.append(output_node)

            # Create edge between machine and machine output node
            graph.edges.append(MachineOutputDirectedEdge(
                start = link_name_to_node_map[machine],
                end = link_name_to_node_map[output_node_name],
                machine_id = machine,
            ))

    # Make edges
    for link in links:
        value = link["value"]
        if math.isclose(value, 0.0):
            continue

        start = link_name_to_node_map[link["start"]]
        end = link_name_to_node_map[link["end"]]
        print(f'{start.id} -> {end.id}')

        item = None
        if isinstance(end, SourceNode):
            item = end.item
        elif isinstance(end, SinkNode):
            item = end.item
        elif isinstance(end, ItemNode):
            item = end.item
        elif isinstance(end, MachineInputNode):
            item = end.item
        elif isinstance(end, MachineOutputNode):
            item = end.item
        else:
            raise ValueError("Invalid node type")

        if type(end) in [SourceNode, SinkNode, ItemNode, MachineInputNode]:
            graph.edges.append(ItemDirectedEdge(
                start = start,
                end = end,
                item = make_item(item),
                quantity = value
            ))

    return graph


def draw(graph: SolutionGraph):

    def make_sources_table(sources: list[SourceNode]):
        table = ''.join([
            '<<table border="0" cellspacing="0">',
            '<tr>',
            *[f'<td border="1" PORT="{source.id}">{source.item} {source.quantity}</td>' for source in sources],
            '</tr>',
            '</table>>',
        ])
        return table

    def make_sinks_table(sinks: list[SinkNode]):
        table = ''.join([
            '<<table border="0" cellspacing="0">',
            '<tr>',
            *[f'<td border="1" PORT="{sink.id}">{sink.item} {sink.quantity}</td>' for sink in sinks],
            '</tr>',
            '</table>>',
        ])
        return table

    def make_machine_table(machine: MachineNode, inputs: list[MachineInputNode], outputs: list[MachineOutputNode]):
        input_table = ''.join([
            '<table border="0" cellspacing="0">',
            '<tr>',
            *[f'<td border="1" bgcolor="#043742" PORT="{input.id}"><FONT color="white">{input.item}</FONT></td>' for input in inputs],
            '</tr>',
            '</table>',
        ])

        output_table = ''.join([
            '<table border="0" cellspacing="0">',
            '<tr>',
            *[f'<td border="1" PORT="{output.id}">{output.item}</td>' for output in outputs],
            '</tr>',
            '</table>',
        ])

        table = ''.join([
            '<<table border="0" cellspacing="0">',
            '<tr>',
            '<td>',
            input_table,
            '</td>',
            '</tr>',
            '<tr>',
            *f'<td border="0" PORT="{machine.id}">{machine.machine_name} x{machine.quantity}</td>',
            '</tr>',
            '<tr>',
            '<td>',
            output_table,
            '</td>',
            '</tr>',
            '</table>>',
        ])
        return table

    # Make the graph
    dot = graphviz.Digraph(comment='GTNH-ToolKit')

    # Style the graph
    dot.attr(rankdir='TB')

    # Source Nodes
    sourcesMap: dict[str, SourceNode] = dict([(node.id, node) for node in graph.nodes if type(node) is SourceNode])
    with dot.subgraph(name='cluster_sources') as subgraph:
        subgraph.attr(rank='source', color='lightgrey', style='filled', pad='0', margin='0')
        subgraph.node('sources', make_sources_table(list(sourcesMap.values())), **{
            'shape': 'plain',
        })
    
    # Sink Nodes
    sinksMap: dict[str, SinkNode] = dict([(node.id, node) for node in graph.nodes if type(node) is SinkNode])
    with dot.subgraph(name='cluster_sinks') as subgraph:
        subgraph.attr(rank='sink', color='lightgrey', style='filled', pad='0', margin='0')
        subgraph.node('sinks', make_sinks_table(list(sinksMap.values())), **{
            'shape': 'plain',
        })

    # Machine Nodes
    machineMap: dict[str, MachineNode] = dict([(node.id, node) for node in graph.nodes if type(node) is MachineNode])
    
    # Machine Input Node
    machineInputsMap: dict[str, list[MachineInputNode]] = defaultdict(list)
    for machineInput in [node for node in graph.nodes if type(node) is MachineInputNode]:
        machineInputsMap[machineInput.machine_id].append(machineInput)
    inputToMachineMap: dict[str, MachineNode] = { v.id: machineMap[k] for (k, list) in machineInputsMap.items() for v in list }

    # Machine Output Nodes
    machineOutputsMap: dict[str, list[MachineOutputNode]] = defaultdict(list)
    for machineOutput in [node for node in graph.nodes if type(node) is MachineOutputNode]:
        machineOutputsMap[machineOutput.machine_id].append(machineOutput)
    outputToMachineMap: dict[str, MachineNode] = { v.id: machineMap[k] for (k, list) in machineOutputsMap.items() for v in list }

    # Combine machine, machine inputs, and machine outputs into 1 table node
    for (machine_id, machineNode) in machineMap.items():
        inputs = machineInputsMap[machine_id]
        outputs = machineOutputsMap[machine_id]
        dot.node(machine_id, make_machine_table(machineNode, inputs, outputs), **{
            'shape': 'plain',
        })

    # Handle ItemNodes
    itemNodeMap: dict[str, ItemNode] = { node.id: node for node in graph.nodes if type(node) is ItemNode }
    for itemNode in itemNodeMap.keys():
        with dot.subgraph(name='regular') as subgraph:
            subgraph.node(itemNode, **{
                'style': 'invis',
                'fixedsize': 'true',
                'width': '0',
                'height': '0',
            })

    # Add the edges
    for edge in graph.edges:
        if type(edge) is ItemDirectedEdge:
            start_id = edge.start.id
            end_id = edge.end.id

            # Sources are prefixed by 'sources:'
            if edge.start.id in sourcesMap:
                start_id = 'sources:' + edge.start.id
            # Sinks are prefixed by 'sinks:'
            if edge.end.id in sinksMap:
                end_id = 'sinks:' + edge.end.id
            # Machine inputs are prefixed by their machine id (e.g. M0:)
            if edge.end.id in inputToMachineMap:
                end_id = f'{inputToMachineMap[edge.end.id].id}:{edge.end.id}'
            # Machine outputs are prefixed by their machine id (e.g. M0:)
            if edge.start.id in outputToMachineMap:
                start_id = f'{outputToMachineMap[edge.start.id].id}:{edge.start.id}'

            labeltext = f'({edge.quantity}/s)'
            headlabel = labeltext if type(edge.end) is not ItemNode else ''
            taillabel = labeltext if type(edge.start) is not ItemNode else ''
            dot.edge(start_id, end_id, **{
                'fontsize': '10',
                'headlabel': headlabel,
                'taillabel': taillabel,
                'labeldistance': '1.1',
            })
            
        elif type(edge) is MachineInputDirectedEdge:
            start_id = f'{edge.machine_id}:{edge.start.id}'
            end_id = f'{edge.machine_id}:{edge.machine_id}'
            with dot.subgraph(name=f'cluster_{edge.machine_id}') as subgraph:
                subgraph.edge(start_id, end_id, '', **{
                    'style': 'invis',
                })

        elif type(edge) is MachineOutputDirectedEdge:
            start_id = f'{edge.machine_id}:{edge.machine_id}'
            end_id = f'{edge.machine_id}:{edge.end.id}'
            with dot.subgraph(name=f'cluster_{edge.machine_id}') as subgraph:
                subgraph.edge(start_id, end_id, '', **{
                    'style': 'invis',
                })

    dot.render('./output/test.gv', format='dot').replace('\\', '/')
    dot.render('./output/test.gv', format='png').replace('\\', '/')
