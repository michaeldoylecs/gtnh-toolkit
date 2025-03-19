from pprint import pprint
import pyomo.environ as pyomo # type: ignore
from configreader import load_factory_config
from grapher import build_solution_graph, draw
from solver import solve
import argparse
import args
    
def main():
    parser = argparse.ArgumentParser(description="Generate GTNH factory diagrams from factory configuration files.")
    parser.add_argument("factory_config", type=str, help="Path to the factory configuration file. (yaml/json)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parsed_args = parser.parse_args()
    
    # Store the parsed arguments in the args module
    args.set_args(parsed_args)

    factory_config_path = args.get_factory_config_path()
    if not factory_config_path:
        print("Factory config not found")
        exit(1)

    factory_config = load_factory_config(factory_config_path)
    if factory_config is None:
        print("Loaded config had errors")
        exit(1)

    model, results, machine_map = solve(factory_config.recipes, factory_config.targets[0])

    # Debug model variables
    if args.is_verbose():
        variables = {v.name.strip("'"): v.value for v in model.component_objects(pyomo.Var, active=True) for v in v.values()}
        pprint(variables)

    graph = build_solution_graph(model, machine_map)
    draw(graph)

if __name__ == "__main__":
    main()
