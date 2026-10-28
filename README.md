# Server Nodes API

A FastAPI application for adding server nodes to a MySQL database.

## Requirements

- Python 3.12 
- uv (For creating virtual environment)

Install the runtime packages:

```terminal;
uv sync
```

## Configure MySQL

Create the database and table if they do not exist:

```sql
CREATE DATABASE servers;

USE servers;

CREATE TABLE nodes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE edges(
  id INT Primary Key AUTO_INCREMENT,
  source_name VARCHAR(100) NOT NULL,
  destination_name VARCHAR(100) NOT NULL,
  latency DOUBLE NOT NULL,           -- CHECK (latency > 0)
  UNIQUE (source_name, destination_name),
  FOREIGN KEY (source_name) REFERENCES nodes(name) ON DELETE CASCADE,
  FOREIGN KEY (destination_name) REFERENCES nodes(name) ON DELETE CASCADE
);
```

## Run the application

From the project root:

```powershell
uv run python main.py
```

## API

### Add a node

http POST /network/nodes-add
Content-Type: application/json


Request body:

json
{
  "name": "edge-server-01"
}

On success, the API responds with HTTP `201` and the inserted row's ID:

json
{
  "id": 1,
  "name": "edge-server-01"
}


Names must be no more than 100 characters. A blank name or an existing name
returns HTTP `400`. A missing `name` field is rejected by request validation.

### List node names

```http
GET /network/nodes
```

The response is a JSON list of names, without node IDs:

```json
["edge-server-01", "edge-server-02"]
```

### Add an edge

```http
POST /network/edges-add
Content-Type: application/json
```

Request body:

```json
{
  "source": "edge-server-01",
  "destination": "edge-server-02",
  "latency": 12.5
}
```

Both named nodes must already exist, latency must be greater than zero, and an
undirected node pair can only be added once. Node names are sorted before
checking and storing the pair, so adding `A`–`B` prevents adding `B`–`A`.
The creation response preserves the order of `source` and `destination` in
the request, even though the pair is stored in sorted order.
Self-loops (where the source and destination identify the same node) are
rejected with HTTP `400`.
Missing or blank source/destination values, latency values less than or equal
to zero, duplicate edges, and references to nodes that do not exist also
return HTTP `400`.
Successful requests return HTTP `201` with the inserted edge ID, source,
destination, and latency.

### Find the lowest-latency path

```http
POST /network/path
Content-Type: application/json
```

Request body:

```json
{
  "source": "ServerA",
  "destination": "ServerD"
}
```

Edges are traversable in both directions. The endpoint returns the path with
the lowest total latency:

```json
{
  "total_latency": 23.4,
  "path": ["ServerA", "ServerB", "ServerD"]
}
```

If either node does not exist or no route connects them, it returns HTTP `404`:

```json
{
  "error": "No path exists between ServerA and ServerD"
}
```