"""
Script to reconfigure the hidden node to join remaining nodes as a 3-node replicaset.
Works on macOS, Linux, and RHEL. Reads MongoDB URI from CLI or config.ini.
"""
import argparse
import configparser
from pymongo import MongoClient
from pathlib import Path

DEFAULT_TARGET_MEMBERS = ["localhost:27020", "localhost:27021", "localhost:27022"]


def get_mongo_uri(cli_uri=None, config_path=None):
    if cli_uri:
        return cli_uri
    cfg_path = Path(config_path) if config_path else Path(__file__).resolve().parent / "config.ini"
    config = configparser.ConfigParser()
    loaded = config.read(cfg_path)
    if not loaded or "mongodb" not in config or "uri" not in config["mongodb"]:
        raise ValueError(f"MongoDB URI not found. Provide --uri or set [mongodb] uri in {cfg_path}")
    return config["mongodb"]["uri"]


def is_member_reachable(host):
    try:
        client = MongoClient(f"mongodb://{host}/?directConnection=true", serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        return True
    except Exception:
        return False


def get_target_members(current_members, explicit_members=None):
    if explicit_members:
        return explicit_members

    reachable = [m["host"] for m in current_members if is_member_reachable(m["host"])]
    if len(reachable) >= 3:
        return reachable[:3]

    return DEFAULT_TARGET_MEMBERS


def reconfig_replset(uri, explicit_members=None):
    client = MongoClient(uri)
    config = client.admin.command("replSetGetConfig")['config']
    target_members = get_target_members(config['members'], explicit_members)

    # Keep exactly 3 members and unhide all of them
    config['members'] = [
        {
            "_id": i,
            "host": host,
            "priority": 1,
            "hidden": False,
            "votes": 1,
        }
        for i, host in enumerate(target_members)
    ]
    config['version'] += 1
    print("Reconfiguring replicaset with:", config)
    client.admin.command("replSetReconfig", config, force=True)
    print("Replicaset reconfigured to 3 nodes.")

def main():
    parser = argparse.ArgumentParser(description="Reconfigure hidden node to join as 3rd node")
    parser.add_argument("--uri", help="MongoDB connection string")
    parser.add_argument("--config", help="Path to INI file containing [mongodb] uri")
    parser.add_argument(
        "--members",
        help="Comma-separated host:port list for new 3-node config (example: localhost:27020,localhost:27021,localhost:27022)",
    )
    args = parser.parse_args()
    uri = get_mongo_uri(args.uri, args.config)
    explicit_members = [m.strip() for m in args.members.split(",")] if args.members else None
    reconfig_replset(uri, explicit_members)

if __name__ == "__main__":
    main()
