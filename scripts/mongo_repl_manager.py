"""
Script to create or destroy a MongoDB replicaset with 5 nodes and 1 hidden node.
Works on macOS, Linux, and RHEL.
"""
import os
import subprocess
import sys
import time
import argparse
from pathlib import Path
import shutil
import json
from typing import List
import psutil

NODE_COUNT = 6  # 5 voting/visible nodes + 1 hidden node
DEFAULT_BASE_PORT = 27017
REPLSET_NAME = "rs0"
DATA_DIR_PREFIX = "mongo-data"
BASE_DIR = Path(__file__).resolve().parent.parent


def run(cmd: List[str], fail_on_error: bool = True):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=False)
    if fail_on_error and result.returncode != 0:
        print(f"Command failed: {' '.join(cmd)}")
        sys.exit(1)
    return result.returncode


def get_ports(base_port: int) -> List[int]:
    return [base_port + i for i in range(NODE_COUNT)]


def get_data_dir_for_port(port: int) -> Path:
    return BASE_DIR / f"{DATA_DIR_PREFIX}-{port}"


def start_nodes(ports: List[int], replset_name: str):
    for port in ports:
        data_dir = get_data_dir_for_port(port)
        os.makedirs(data_dir, exist_ok=True)
        run([
            "mongod",
            "--replSet",
            replset_name,
            "--port",
            str(port),
            "--dbpath",
            str(data_dir),
            "--bind_ip",
            "localhost",
            "--fork",
            "--logpath",
            str(data_dir / "mongod.log"),
        ])
    print("All nodes started.")


def initiate_replset(ports: List[int], replset_name: str):
    config = {
        "_id": replset_name,
        "members": [
            {"_id": i, "host": f"localhost:{port}", "priority": 1 if i < 5 else 0, "hidden": True if i == 5 else False}
            for i, port in enumerate(ports)
        ]
    }
    print("Initiating replicaset with config:", config)

    config_json = json.dumps(config)
    init_cmd = f"rs.initiate({config_json})"

    shell = "mongosh"
    if shutil.which(shell) is None:
        shell = "mongo"

    run([shell, "--quiet", "--port", str(ports[0]), "--eval", init_cmd])
    print("Replicaset initiated.")


def stop_nodes(ports: List[int]):
    target_ports = set(ports)
    found = []

    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            name = (proc.info.get("name") or "").lower()
            if "mongod" not in name:
                continue

            cmdline = proc.info.get("cmdline") or []
            for idx, arg in enumerate(cmdline):
                if arg == "--port" and idx + 1 < len(cmdline):
                    try:
                        port = int(cmdline[idx + 1])
                    except ValueError:
                        continue

                    if port in target_ports:
                        print(f"Stopping mongod on port {port} (pid {proc.pid})")
                        proc.terminate()
                        found.append(proc)
                        break
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    gone, alive = psutil.wait_procs(found, timeout=8)
    for proc in alive:
        try:
            print(f"Force killing mongod pid {proc.pid}")
            proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    print("All nodes stopped.")


def destroy_data(ports: List[int]):
    for port in ports:
        data_dir = get_data_dir_for_port(port)
        if data_dir.exists():
            shutil.rmtree(data_dir)
    print("All data directories removed.")


def main():
    parser = argparse.ArgumentParser(description="MongoDB Replicaset Manager")
    parser.add_argument("action", choices=["create", "destroy"], help="Action to perform")
    parser.add_argument("--base-port", type=int, default=DEFAULT_BASE_PORT, help="Starting port for 6 mongod nodes")
    parser.add_argument("--replset", default=REPLSET_NAME, help="Replica set name")
    args = parser.parse_args()
    ports = get_ports(args.base_port)

    if args.action == "create":
        start_nodes(ports, args.replset)
        time.sleep(3)
        initiate_replset(ports, args.replset)
    elif args.action == "destroy":
        stop_nodes(ports)
        destroy_data(ports)

if __name__ == "__main__":
    main()
