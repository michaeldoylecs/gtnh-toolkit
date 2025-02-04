import pyomo.environ as pyomo # type: ignore
from grapher import build_solution_graph, draw
from models import GameTicks, ItemStack, Recipe, TargetRate, make_item
from solver import solve
    
def main():
    # Dummy data
    recipe_hydrogen = Recipe(
        inputs = [
            ItemStack(make_item("water"), 500)
        ],
        outputs = [
            ItemStack(make_item("oxygen"), 500),
            ItemStack(make_item("hydrogen"), 1000)
        ],
        duration = GameTicks(1000),
        eu_per_gametick = 100,
    )
    recipe_hydrogen_sulfude = Recipe(
        inputs = [
            ItemStack(make_item("sulfur"), 1),
            ItemStack(make_item("hydrogen"), 2000)
        ],
        outputs = [
            ItemStack(make_item("hydrogen sulfide"), 1000)
        ],
        duration = GameTicks(60),
        eu_per_gametick = 200,
    )

    target: TargetRate = TargetRate(
        item = make_item("hydrogen sulfide"),
        quantity_per_second = 5000 / 20,
    )

    model, results = solve([recipe_hydrogen, recipe_hydrogen_sulfude], target)

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
