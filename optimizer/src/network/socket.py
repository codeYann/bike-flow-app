import socket
import redis

def start_socket_server(client: redis.Redis, host="localhost", port=65432):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen()
            print(f"Server listening on {host}:{port}")
            conn, addr = s.accept()
            with conn:
                print(f"Connected by {addr}")
                while True:
                    try:
                        data = conn.recv(1024)
                        if not data:
                            break
                        instance_key = data.decode("utf-8")
                        value = client.get(instance_key)
                        if value is not None:
                            response = f"Key: {instance_key}, Content: {value.decode('utf-8')}"
                        else:
                            response = f"Key: {instance_key} not found in Redis"
                        conn.sendall(response.encode("utf-8"))
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Error during data processing: {e}")
                        conn.sendall(b"An error occurred while processing your request.")
    except socket.error as e:
        print(f"Socket error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
