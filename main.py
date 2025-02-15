import pyomo.environ as pyomo # type: ignore
from configreader import load_factory_config
from grapher import build_solution_graph, draw
from solver import solve
    
def main():
    # Dummy data.
    factory_config = load_factory_config("./.input/hydrogen_sulfide.json")

    if factory_config is None:
        print("Loaded config had errors")
        exit(1)
    model, results = solve(factory_config.recipes, factory_config.targets[0])

    # Print the results
    model.pprint()
    print(results)
    for v in model.component_objects(pyomo.Var, active=True):
        varobject = getattr(model, str(v))
        print(f"{v} = {varobject.value}")

    graph = build_solution_graph(model)
    print(graph.nodes)
    print(graph.edges)

    draw(graph)

if __name__ == "__main__":
    main()
