from pprint import pprint
import pyomo.environ as pyomo # type: ignore
from configreader import load_factory_config
from grapher import build_solution_graph, draw
from solver import solve
import argparse
    
def main():
    parser = argparse.ArgumentParser(description="Generate GTNH factory diagrams from factory configuration files.")
    parser.add_argument("file_path", type=str, help="Path to the factory configuration file. (yaml/json)")
    args = parser.parse_args()

    factory_config = load_factory_config(args.file_path)
    if factory_config is None:
        print("Loaded config had errors")
        exit(1)
    model, results, machine_map = solve(factory_config.recipes, factory_config.targets[0])

    # Debug model variables
    variables = {v.name.strip("'"): v.value for v in model.component_objects(pyomo.Var, active=True) for v in v.values()}
    pprint(variables)

    graph = build_solution_graph(model, machine_map)
    draw(graph)

if __name__ == "__main__":
    main()
