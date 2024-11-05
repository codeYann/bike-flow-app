from itertools import product
from typing import Any, Dict, List, Set, Tuple
import mip  # type: ignore
import networkx as nx  # type: ignore
import numpy as np


class UserCutCallbacks(mip.ConstrsGenerator):
    def __init__(
        self,
        vertices: Set[int],
        arcs: Dict[Tuple[int, int], Any],
        demands: List[int],
        vehicle_capacity: int,
        x: Dict[Tuple[int, int], mip.Var],
    ):
        self.vertices = vertices
        self.arcs = arcs
        self.demands = demands
        self.vehicle_capacity = vehicle_capacity
        self.x = x

    def generate_constrs(self, model: mip.Model, depth: int = 0, npass: int = 0):
        vertices = self.vertices
        depot = 0
        y = model.translate(self.x)
        cp = mip.CutPool()

        G_prime = nx.DiGraph()
        G_prime.add_nodes_from(vertices)

        arcs_prime = [
            (i, j) for i, j in product(vertices, vertices) if i != j and y[i, j]
        ]

        for u, v in arcs_prime:
            if y[u, v].x > 0:
                G_prime.add_edge(u, v, capacity=y[u, v].x)

        for node in vertices - {depot}:
            try:
                flow = nx.maximum_flow_value(G_prime, depot, node)
            except Exception as error:
                print(error)

            if flow < 1:
                _, (S, _) = nx.minimum_cut(G_prime, depot, node)
                S = S - {0}
                if len(S) != 0:
                    tour = [
                        (y[i, j], y[i, j].x)
                        for i, j in product(S, S)
                        if i != j and y[i, j]
                    ]
                    if sum(value for _, value in tour) >= len(S) - 1:
                        cut = mip.xsum(1 * var for var, _ in tour) <= len(S) - 1
                        cp.add(cut)

                    total_demand_on_S = np.abs(sum(self.demands[i] for i in S))
                    min_vehicles_to_serve_S = np.ceil(
                        total_demand_on_S / self.vehicle_capacity
                    )

                    if sum(value for _, value in tour) >= len(S) - max(
                        1, min_vehicles_to_serve_S
                    ):
                        cut = mip.xsum(1 * var for var, _ in tour) <= len(S) - max(
                            1, min_vehicles_to_serve_S
                        )
                        cp.add(cut)
        for cut in cp.cuts:
            model += cut
