import os
import socket
import time
from database.connection import get_redis_client
from database.redis_operations import load_json_to_redis
from network.socket import start_socket_server

current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, "data")

client = get_redis_client()

load_json_to_redis(data_path, client)


if __name__ == "__main__":
    start_socket_server(client=client)
