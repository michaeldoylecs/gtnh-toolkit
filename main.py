from configreader import load_factory_config
from grapher import build_solution_graph, draw
from solver import solve
    
def main():
    # Dummy data.
    factory_config = load_factory_config("./.input/naq_fuel_mk1.yaml")

    if factory_config is None:
        print("Loaded config had errors")
        exit(1)
    model, results, machine_map = solve(factory_config.recipes, factory_config.targets[0])

    graph = build_solution_graph(model, machine_map)
    draw(graph)

if __name__ == "__main__":
    main()
