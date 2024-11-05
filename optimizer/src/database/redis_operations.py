import json
import os
import redis
import logging
from typing import Optional


def load_json_to_redis(
    data_folder: str, client: redis.Redis, ttl: Optional[int] = None
):
    """
    Load JSON files from a specified folder into Redis.

    Parameters:
    - data_folder (str): Path to the folder containing JSON files.
    - client (redis.Redis): Redis client instance.
    - ttl (Optional[int]): Time-to-live for each key in seconds (default is no expiration).
    """
    logging.basicConfig(level=logging.INFO)

    # Verify Redis connection before processing files
    try:
        if not client.ping():
            logging.error("Failed to connect to Redis.")
            raise redis.ConnectionError("Failed to connect to Redis.")
    except redis.ConnectionError as e:
        logging.error(f"Redis connection error: {e}")
        raise

    # Iterate through JSON files in the folder
    for filename in os.listdir(data_folder):
        if filename.endswith(".json"):
            file_path = os.path.join(data_folder, filename)
            try:
                with open(file_path, "r") as file:
                    instance = json.load(file)

                key = os.path.splitext(filename)[0]
                
                if ttl:
                    client.setex(key, ttl, json.dumps(instance))
                else:
                    client.set(key, json.dumps(instance))

                logging.info(
                    f"Successfully loaded {filename} into Redis with key: {key}"
                )

            except json.JSONDecodeError as e:
                logging.error(f"Failed to decode JSON from {filename}: {e}")
                raise
            except FileNotFoundError as e:
                logging.error(f"File not found: {filename}")
                raise
            except OSError as e:
                logging.error(f"OS error when processing {filename}: {e}")
                raise
            except redis.RedisError as e:
                logging.error(f"Redis error with key {key}: {e}")
                raise
