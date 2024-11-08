import os
import json
import socket
import logging
import mip  # type: ignore
import numpy as np
from model.heuristics import closest_neighbor
from model.cut_callbacks import UserCutCallbacks
from typing import Dict, Tuple, List, Set

current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "data")


def read_json_file(data_path: str, filename: str) -> dict:
    """Reads a JSON file from the data directory."""
    json_file = f"{filename}.json"
    file_path = os.path.join(data_path, json_file)
    try:
        with open(file_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error(f"File {filename} not found in data directory.")
        raise
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from file {filename}: {e}")
        raise


def generate_initial_solution(
    stations: Set[int],
    demands: List[int],
    distance_matrix: np.matrix,
    vehicle_capacity: int,
    x: Dict[Tuple[int, int], mip.Var],
) -> List[Tuple[mip.Var, int]]:
    """Generates an initial solution using the closest neighbor heuristic."""
    depot = 0
    customers = list(stations - {depot})
    demand_dict = dict(enumerate(demands))
    routes = closest_neighbor(
        depot, customers, demand_dict, distance_matrix, vehicle_capacity
    )

    initial_solution = [
        (x[i, j], 1) for route in routes for i, j in zip(route, route[1:])
    ]
    return initial_solution


def setup_model(
    instance_json: dict,
) -> Tuple[mip.Model, Dict[Tuple[int, int], mip.Var], Dict[Tuple[int, int], mip.Var]]:
    """Sets up the MIP model based on the instance data."""
    V = set(range(instance_json["num_vertices"]))
    A = {(i, j): instance_json["distance_matrix"][i][j] for i in V for j in V}

    m = 3
    Q = instance_json["vehicle_capacity"]
    q = instance_json["demands"]

    model = mip.Model(sense=mip.MINIMIZE, solver_name=mip.CBC)
    x = {(i, j): model.add_var(name=f"x_{i}_{j}", var_type=mip.BINARY) for (i, j) in A}
    f = {
        (i, j): model.add_var(name=f"f_{i}_{j}", var_type=mip.CONTINUOUS)
        for i in V
        for j in V
    }

    model.objective = mip.xsum(cost * x[i, j] for (i, j), cost in A.items())
    model += mip.xsum(x[i, i] for i in V) == 0

    for j in V - {0}:
        model += mip.xsum(x[i, j] for i in V) == 1  # Inflow
        model += mip.xsum(x[j, i] for i in V) == 1  # Outflow

    model += mip.xsum(x[0, j] for j in V - {0}) <= m  # Vehicle limit
    model += (
        mip.xsum(x[0, j] for j in V - {0}) - mip.xsum(x[j, 0] for j in V - {0}) == 0
    )  # Return to depot

    model += mip.xsum(f[i, i] for i in V) == 0

    for j in V - {0}:
        model += (
            mip.xsum(f[j, i] for i in V if i != j)
            - mip.xsum(f[i, j] for i in V if i != j)
            == q[j]
        )

    for i in V:
        for j in V:
            if i != j:
                flow_lower_bound = max(0, q[i], -q[j]) * x[i, j]
                flow_upper_bound = min(Q, Q + q[i], Q - q[j]) * x[i, j]
                model += f[i, j] >= flow_lower_bound
                model += f[i, j] <= flow_upper_bound

    return model, x, f


def handle_client(socket_client: socket.socket, data_path: str):
    """Handles communication with a connected client."""
    try:
        instance_key = socket_client.recv(1024).decode("utf-8").strip()
        if not instance_key:
            return

        try:
            instance_json = read_json_file(data_path, instance_key)
            model, x, f = setup_model(instance_json)

            V = set(range(instance_json["num_vertices"]))
            A = {(i, j): instance_json["distance_matrix"][i][j] for i in V for j in V}
            q = instance_json["demands"]
            c = instance_json["distance_matrix"]
            Q = instance_json["vehicle_capacity"]

            initial_solution = generate_initial_solution(V, q, np.matrix(c), Q, x)
            model.start = initial_solution
            model.cuts_generator = UserCutCallbacks(V, A, q, Q, x)
            model.optimize(max_seconds=300)

            if model.num_solutions:
                route = [
                    (origin, destination, f[origin, destination].x)
                    for origin in V
                    for destination in V
                    if x[origin, destination].x == 1 and f[origin, destination]
                ]

                data = {"routes": route}
                json_response = json.dumps(data)
                socket_client.send(json_response.encode("utf-8"))

        except FileNotFoundError:
            error_message = f"Instance {instance_key} not found."
            logging.error(error_message)
            socket_client.sendall(error_message.encode("utf-8"))

    except socket.timeout:
        logging.info("Connection timed out")
    except socket.error as e:
        logging.error(f"Socket error: {e}")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
    finally:
        socket_client.close()


def start_server(host: str, port: int):
    """Starts the server to listen for incoming connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind((host, port))
        server.listen()
        logging.info(f"Server listening on {host}:{port}")

        while True:
            socket_client, addr = server.accept()
            logging.info(f"Connected by {addr}")
            handle_client(socket_client, data_path)


if __name__ == "__main__":
    start_server("localhost", 65432)
