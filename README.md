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
```

## Run the application

From the project root:

```powershell
python main.py
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