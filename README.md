# MongoDB Replicaset Automation

This project provides Python scripts to automate the creation, management, and testing of a MongoDB replicaset with 5 nodes and 1 hidden node. Scripts are cross-platform (macOS, Linux, RHEL) and configurable via CLI or config file.

## Features
- **Create/Destroy Replicaset**: Start or destroy a 5-node + 1 hidden node MongoDB replicaset locally.
- **Read/Write Driver**: Simulate configurable read/write load (default 30 ops/sec) with majority write concern.
- **Kill Nodes**: Kill 3 MongoDB nodes by port.
- **Reconfigure Hidden Node**: Promote hidden node to join remaining nodes as a 3-node replicaset.
- **Configurable**: All scripts accept MongoDB URI via CLI or `config.ini`.

## Requirements
- Python 3.7+
- MongoDB binaries (`mongod`, `mongo` in PATH)
- [pymongo](https://pypi.org/project/pymongo/), [psutil](https://pypi.org/project/psutil/)

Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### 1. Create or Destroy Replicaset
```bash
python scripts/mongo_repl_manager.py create   # Start 5+1 nodes and initiate replicaset
python scripts/mongo_repl_manager.py destroy  # Stop all nodes and remove data
```

### 2. Read/Write Driver
```bash
python scripts/mongo_driver.py --rate 30 --uri <mongodb-uri>
# Or use INI file (defaults to scripts/config.ini)
python scripts/mongo_driver.py --rate 30 --config scripts/config.ini
```

### 3. Kill 3 Nodes
```bash
python scripts/kill_nodes.py --ports 27017 27018 27019
# Or auto-pick first 3 hosts from URI/INI
python scripts/kill_nodes.py --uri <mongodb-uri>
python scripts/kill_nodes.py --config scripts/config.ini
```

### 4. Reconfigure Hidden Node
```bash
python scripts/reconfig_hidden.py --uri <mongodb-uri>
# Or use INI file and explicit members
python scripts/reconfig_hidden.py --config scripts/config.ini
python scripts/reconfig_hidden.py --uri <mongodb-uri> --members localhost:27020,localhost:27021,localhost:27022
```

## Configuration
Edit `scripts/config.ini` to set your MongoDB connection string.
All scripts read `scripts/config.ini` by default and can be overridden with `--config`.

## Notes
- Scripts are designed for local testing/dev only.
- For production, use proper orchestration and security.
- Scripts are extendable for other OSes and cluster topologies.

## .gitignore
See `.gitignore` for files/folders to exclude (Python cache, MongoDB data, etc).

---

**Author:** Your Name
