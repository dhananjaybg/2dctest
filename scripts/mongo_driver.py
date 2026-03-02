"""
Driver script to perform configurable read/write ops on MongoDB replicaset.
Works on macOS, Linux, and RHEL. Reads MongoDB URI from CLI or config.ini.
"""
import argparse
import configparser
import threading
import time
from pathlib import Path
from pymongo import MongoClient, WriteConcern
from pymongo.errors import PyMongoError
import random

def get_mongo_uri(cli_uri=None, config_path=None):
    if cli_uri:
        return cli_uri
    cfg_path = Path(config_path) if config_path else Path(__file__).resolve().parent / "config.ini"
    config = configparser.ConfigParser()
    loaded = config.read(cfg_path)
    if not loaded or "mongodb" not in config or "uri" not in config["mongodb"]:
        raise ValueError(f"MongoDB URI not found. Provide --uri or set [mongodb] uri in {cfg_path}")
    return config["mongodb"]["uri"]

def writer(client, rate):
    db = client.testdb
    coll = db.testcoll.with_options(write_concern=WriteConcern(w="majority"))
    while True:
        doc = {"ts": time.time(), "val": random.randint(1, 100000)}
        try:
            coll.insert_one(doc)
        except PyMongoError as e:
            print(f"Write error: {e}")
        time.sleep(1/rate)

def reader(client, rate):
    db = client.testdb
    coll = db.testcoll
    while True:
        try:
            _ = list(coll.find().limit(5))
        except PyMongoError as e:
            print(f"Read error: {e}")
        time.sleep(1/rate)

def main():
    parser = argparse.ArgumentParser(description="MongoDB driver for read/write ops")
    parser.add_argument("--uri", help="MongoDB connection string")
    parser.add_argument("--config", help="Path to INI file containing [mongodb] uri")
    parser.add_argument("--rate", type=int, default=30, help="Ops per second (default: 30)")
    args = parser.parse_args()
    if args.rate <= 0:
        raise ValueError("--rate must be > 0")
    uri = get_mongo_uri(args.uri, args.config)
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    t1 = threading.Thread(target=writer, args=(client, args.rate))
    t2 = threading.Thread(target=reader, args=(client, args.rate))
    t1.daemon = True
    t2.daemon = True
    t1.start()
    t2.start()
    print(f"Running {args.rate} reads & writes/sec. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting.")

if __name__ == "__main__":
    main()
