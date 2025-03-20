import abc
from collections import defaultdict
from dataclasses import dataclass, field
import itertools
import math
import re
import graphviz # type: ignore
import pyomo.environ as pyomo # type: ignore

import args
from models import Item, Recipe, make_item

EDGE_COLOR_ITERATOR = itertools.cycle([
    '#b58900', # 'yellow'
    '#cb4b16', # 'orange'
    '#dc322f', # 'red'
    '#d33682', # 'magenta'
    '#6c71c4', # 'violet'
    '#268bd2', # 'blue'
    '#2aa198', # 'cyan'
    '#859900', # 'green'
])

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
    recipe: Recipe

    def __init__(self, id: str, machine_name: str, quantity: float, recipe: Recipe):
        self.machine_name = machine_name
        self.quantity = quantity
        self.recipe = recipe
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

def build_solution_graph(model: pyomo.Model, machine_id_to_recipe_map: dict[str, Recipe]) -> SolutionGraph:
    graph = SolutionGraph()

    # Extract variable names and values
    variables = {v.name.strip("'"): v.value for v in model.component_objects(pyomo.Var, active=True) for v in v.values()}
    
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

    # Print filtered variables if verbose mode is enabled
    if args.is_verbose():
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
            machine_id, = match.groups()
            recipe = machine_id_to_recipe_map[machine_id]
            machine_name = recipe.machine_name
            machine_node = MachineNode(
                id = machine,
                machine_name = machine_name,
                quantity = quantity,
                recipe = recipe,
            )
            machine_nodes[machine_id] = machine_node
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
    def applySISymbols(number: float) -> str:
        suffixes = ['', 'k', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'R', 'Q']

        # Cannot take the log10 of 0
        if number == 0:
            return '0'
        
        degree = int(math.floor(math.log10(math.fabs(number)) / 3))
        
        if degree < len(suffixes):
            suffix = suffixes[degree]
            scaled_number = float(number * math.pow(1000, -degree))
        else:
            suffix = suffixes[-1]
            scaled_number = float(number * math.pow(1000, -(len(suffixes) - 1)))
        
        formatted_number = '{:,.2f}'.format(scaled_number)
        return f'{formatted_number}{suffix}'

    def make_sources_table(sources: list[SourceNode]):
        table = ''.join([
            '<<table border="0" cellspacing="0" bgcolor="lightgrey">',
            '<tr>',
            *[f'<td border="1" PORT="{source.id}">{source.item}</td>' for source in sources],
            '</tr>',
            '</table>>',
        ])
        return table

    def make_sinks_table(sinks: list[SinkNode]):
        table = ''.join([
            '<<table border="0" cellspacing="0">',
            '<tr>',
            *[f'<td border="1" PORT="{sink.id}">{sink.item}</td>' for sink in sinks],
            '</tr>',
            '</table>>',
        ])
        return table

    def make_machine_table(machine: MachineNode, inputs: list[MachineInputNode], outputs: list[MachineOutputNode]):
        input_table = ''.join([
            '<table border="0" cellspacing="0">',
            '<tr>',
            *([f'<td border="1" bgcolor="#0a5161" PORT="{input.id}"><FONT color="white">{input.item}</FONT></td>' for input in inputs] if inputs else '<td></td>'),
            '</tr>',
            '</table>',
        ])

        machine_eu_amortized = applySISymbols(machine.recipe.eu_per_gametick * machine.quantity)
        eu_per_machine = applySISymbols(machine.recipe.eu_per_gametick)
        machine_table = ''.join([
            '<table border="0" bgcolor="white" cellspacing="0">',
            '<tr>',
            f'<td border="0" PORT="{machine.id}">{'{:,.2f}'.format(machine.quantity)}x {machine.machine_name}</td>',
            '</tr>',
            '<tr>',
            f'<td border="0">Recipe time: {'{:,.2f}'.format(machine.recipe.duration / 20)}s</td>'
            '</tr>',
            '<tr>',
            f'<td border="0">EU Amortized: {machine_eu_amortized} EU/t</td>'
            '</tr>',
            '<tr>',
            f'<td border="0">EU per Machine: {eu_per_machine} EU/t</td>'
            '</tr>',
            '</table>',
        ])

        output_table = ''.join([
            '<table border="0" cellspacing="0">',
            '<tr>',
            *([f'<td border="1" bgcolor="#0a5161" PORT="{output.id}"><FONT color="white">{output.item}</FONT></td>' for output in outputs] if outputs else '<td></td>'),
            '</tr>',
            '</table>',
        ])

        table = ''.join([
            '<<table border="0" cellpadding="0" cellspacing="0">',
            '<tr>',
            '<td border="0" cellpadding="0" cellspacing="0">',
            input_table,
            '</td>',
            '</tr>',
            '<tr>',
            '<td border="1" cellpadding="0" cellspacing="0">',
            machine_table,
            '</td>',
            '</tr>',
            '<tr>',
            '<td border="0" cellpadding="0" cellspacing="0">',
            output_table,
            '</td>',
            '</tr>',
            '</table>>',
        ])
        return table
    
    def make_overview_table() -> str:
        overview = ''.join([
            '<<table border="0" cellpadding="0" cellspacing="0" bgcolor="white">',
                '<tr>',
                    '<td border="1" cellpadding="4" cellspacing="0">',
                        '<b>Factory Overview</b>',
                    '</td>',
                '</tr>',
            '</table>>',
        ])
        return overview

    # Make the graph
    dot = graphviz.Digraph(comment='GTNH-ToolKit')

    # Style the graph
    dot.attr(
        bgcolor='#043742',
        rankdir='TB',
        ranksep='1.25',
        nodesed='0.25',
    )

    # Source Nodes
    sourcesMap: dict[str, SourceNode] = dict([(node.id, node) for node in graph.nodes if type(node) is SourceNode])
    with dot.subgraph(name='cluster_sources') as subgraph:
        subgraph.attr(rank='source', pad='0', margin='0', rankdir='LR', peripheries='0')
        subgraph.node('sources', make_sources_table(list(sourcesMap.values())), **{
            'shape': 'plain',
            'margin': '0',
            'peripheries': '0',
        })
    
    # Add overview node separately
    dot.node('overview', make_overview_table(), **{
        'shape': 'plain',
        'margin': '0',
        'peripheries': '0',
    })
    
    # Position overview to the right of sources using a horizontal layout
    dot.attr(newrank='true')  # Enable newrank feature for better ranking
    with dot.subgraph(name='cluster_top_row') as top_row:
        top_row.attr(rank='source', peripheries='0')
        # Use invisible nodes with the same names to control positioning
        # without affecting the actual nodes
        top_row.node('_sources', style='invis', width='0')
        top_row.node('_overview', style='invis', width='0')
        # Add invisible edge to position overview to the right of sources
        top_row.edge('_sources', '_overview', style='invis', constraint='true', weight='100')
        # Connect invisible nodes to real nodes to influence their positions
        dot.edge('_sources', 'sources', style='invis', constraint='false')
        dot.edge('_overview', 'overview', style='invis', constraint='false')
    
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

    # Machine Output Nodes
    machineOutputsMap: dict[str, list[MachineOutputNode]] = defaultdict(list)
    for machineOutput in [node for node in graph.nodes if type(node) is MachineOutputNode]:
        machineOutputsMap[machineOutput.machine_id].append(machineOutput)

    # Combine machine, machine inputs, and machine outputs into 1 table node
    for (machine_id, machineNode) in machineMap.items():
        inputs = machineInputsMap[machine_id]
        outputs = machineOutputsMap[machine_id]
        with dot.subgraph(name=f'cluster_{machine_id}') as subgraph:
            subgraph.attr(**{
                'margin': '0',
                'peripheries': '0',
            })
            subgraph.node(machine_id, make_machine_table(machineNode, inputs, outputs), **{
                'shape': 'plain',
                'margin': '0',
            })

    # Get directed edges
    item_directed_edges: list[ItemDirectedEdge] = [edge for edge in graph.edges if type(edge) is ItemDirectedEdge]

    # Get machine input edges
    machine_input_edges: list[MachineInputDirectedEdge] = [edge for edge in graph.edges if type(edge) is MachineInputDirectedEdge]

    # Get machine output edges
    machine_output_edges: list[MachineOutputDirectedEdge] = [edge for edge in graph.edges if type(edge) is MachineOutputDirectedEdge]
    
    # Group together ItemNodes and their connecting edges.
    # If an edge does not connect to an ItemNode, add it to another list for processing
    itemNodeMap: dict[str, ItemNode] = { node.id: node for node in graph.nodes if type(node) is ItemNode }
    itemNodeConnectedEdges: dict[str, list[ItemDirectedEdge]] = defaultdict(list)
    edges_without_item_nodes: list[ItemDirectedEdge] = []
    for edge in item_directed_edges:
        startItemNode = itemNodeMap.get(edge.start.id)
        endItemNode = itemNodeMap.get(edge.end.id)
        if startItemNode:
            itemNodeConnectedEdges[startItemNode.id].append(edge)
        elif endItemNode:
            itemNodeConnectedEdges[endItemNode.id].append(edge)
        else:
            edges_without_item_nodes.append(edge)

    # Draw edges connected to ItemNodes
    for item_node_id, item_edges in itemNodeConnectedEdges.items():
        # If a node has only 2 connected edges, the node is redundant and the 2 edges
        # can be combined into 1.
        if len(item_edges) == 2:
            start = item_edges[0].start
            end = item_edges[1].end

            if type(start) is ItemNode:
                start = item_edges[1].start
                end = item_edges[0].end

            combined_edge = ItemDirectedEdge(
                start = start,
                end = end,
                item = item_edges[0].item,
                quantity = item_edges[0].quantity,
            )
            edges_without_item_nodes.append(combined_edge)
            continue

        edge_color = next(EDGE_COLOR_ITERATOR)
        with dot.subgraph(name='regular') as subgraph:
            subgraph.node(item_node_id, **{
                'shape': 'point',
                'width': '0.03',
                'height': '0.03',
                'color': edge_color,
            })
        
        for edge in item_edges:
            draw_item_edge(dot, edge, edge_color)

    # Connect edges without ItemNodes
    for edge in edges_without_item_nodes:
        draw_item_edge(dot, edge, next(EDGE_COLOR_ITERATOR))

    # Build machine input edges
    for input_edge in machine_input_edges:
        start_id = f'{input_edge.machine_id}:{input_edge.start.id}'
        end_id = f'{input_edge.machine_id}:{input_edge.machine_id}'
        with dot.subgraph(name=f'cluster_{input_edge.machine_id}') as subgraph:
            subgraph.edge(start_id, end_id, '', **{
                'style': 'invis',
                'margin': '0',
            })

    # Build machine output edges
    for output_edge in machine_output_edges:
        start_id = f'{output_edge.machine_id}:{output_edge.machine_id}'
        end_id = f'{output_edge.machine_id}:{output_edge.end.id}'
        with dot.subgraph(name=f'cluster_{output_edge.machine_id}') as subgraph:
            subgraph.edge(start_id, end_id, '', **{
                'style': 'invis',
                'margin': '0',
            })
    try:
        dot.render('./output/test.gv', format='dot', quiet=False)
        dot.render('./output/test.gv', format='png', quiet=False)
    except graphviz.CalledProcessError as e:
        print("Graphviz Error:")
        print("Return Code:", e.returncode)
        print("Command:", e.cmd)
        print("Output:", e.output.decode("utf-8") if e.output else "No output")
        print("Error Message:", e.stderr.decode("utf-8") if e.stderr else "No error message")

def draw_item_edge(dot: graphviz.Digraph, edge: ItemDirectedEdge, color: str):
    start_id = edge.start.id
    end_id = edge.end.id

    # Sources are prefixed by 'sources:'
    if type(edge.start) is SourceNode:
        start_id = 'sources:' + edge.start.id + ':s'
    # Sinks are prefixed by 'sinks:'
    if type(edge.end) is SinkNode:
        end_id = 'sinks:' + edge.end.id + ':n'
    # Machine inputs are prefixed by their machine id (e.g. M0:)
    if type(edge.end) is MachineInputNode:
        end_id = f'{edge.end.machine_id}:{edge.end.id}:n'
    # Machine outputs are prefixed by their machine id (e.g. M0:)
    if type(edge.start) is MachineOutputNode:
        start_id = f'{edge.start.machine_id}:{edge.start.id}:s'

    labeltext = f'({'{:,.2f}'.format(edge.quantity)}/s)'
    headlabel = labeltext if type(edge.end) is not ItemNode else ''
    taillabel = labeltext if type(edge.start) is not ItemNode else ''
    arrowhead = 'normal' if type(edge.end) is not ItemNode else 'none'
    arrowtail = 'tee' if type(edge.start) is not ItemNode else 'none'
    edge_color = color
    dot.edge(start_id, end_id, **{
        'fontsize': '10',
        'fontcolor': edge_color,
        'headlabel': headlabel,
        'taillabel': taillabel,
        'labeldistance': '2.8',
        'labelangle': '60',
        'arrowhead': arrowhead,
        'arrowtail': arrowtail,
        'color': edge_color,
    })
