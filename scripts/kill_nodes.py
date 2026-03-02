"""
Script to kill MongoDB nodes by terminating their processes.
Works on macOS, Linux, and RHEL. Reads MongoDB ports from config or default.
"""
import argparse
import os
import signal
import psutil
import configparser
from pathlib import Path
from pymongo.uri_parser import parse_uri

MONGO_PORTS = [27017, 27018, 27019, 27020, 27021, 27022]


def get_mongo_uri(cli_uri=None, config_path=None):
    if cli_uri:
        return cli_uri
    cfg_path = Path(config_path) if config_path else Path(__file__).resolve().parent / "config.ini"
    config = configparser.ConfigParser()
    loaded = config.read(cfg_path)
    if not loaded or "mongodb" not in config or "uri" not in config["mongodb"]:
        return None
    return config["mongodb"]["uri"]


def get_ports_from_uri(uri):
    if not uri:
        return []
    parsed = parse_uri(uri)
    return [int(port) for _, port in parsed.get("nodelist", []) if port]

def kill_nodes(ports_to_kill):
    killed = set()
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            process_name = (proc.info.get('name') or '').lower()
            cmdline = proc.info.get('cmdline') or []
            if 'mongod' in process_name:
                cmd = ' '.join(cmdline)
                for port in ports_to_kill:
                    if f'--port {port}' in cmd:
                        print(f"Stopping mongod on port {port}, pid {proc.pid}")
                        os.kill(proc.pid, signal.SIGTERM)
                        killed.add(port)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return sorted(killed)

def main():
    parser = argparse.ArgumentParser(description="Kill MongoDB nodes")
    parser.add_argument('--ports', nargs='+', type=int, help='Specific node ports to kill (example: --ports 27018 27021)')
    parser.add_argument('--uri', help='MongoDB connection string')
    parser.add_argument('--config', help='Path to INI file containing [mongodb] uri')
    args = parser.parse_args()
    if args.ports:
        ports = sorted(set(args.ports))
    else:
        uri = get_mongo_uri(args.uri, args.config)
        ports_from_uri = get_ports_from_uri(uri)
        ports = ports_from_uri[:3] if ports_from_uri else MONGO_PORTS[:3]
    killed_ports = kill_nodes(ports)
    print(f"Requested kill ports: {ports}")
    print(f"Actually stopped ports: {killed_ports}")

if __name__ == "__main__":
    main()
