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

CREATE TABLE route_history (
    id BIGINT PRIMARY KEY AUTO_INCREMENT,
    source VARCHAR(100) NOT NULL,
    destination VARCHAR(100) NOT NULL,
    total_latency DOUBLE NOT NULL,
    path JSON NOT NULL,
    username VARCHAR(255) NOT NULL,
    created_at DATETIME(6) NOT NULL,
    INDEX idx_route_history_created_at (created_at)
);
```

If the database already exists, create the `route_history` table before
deploying this version; the application does not create or migrate tables
automatically.

## JWT authorization

This app uses a single configured account for login. The username and password
are read from environment variables; passwords are not stored in the database
by this environment-based setup. FastAPI exposes the bearer-token flow as
OAuth2 password bearer authentication, and access tokens are signed JWTs using
HS256.

1. Copy the example configuration to a local, ignored file:

   ```powershell
   Copy-Item .env.example .env.local
   ```

2. Set `DATABASE_URL` to your MySQL connection, and set `AUTH_USERNAME` and a
   unique `AUTH_PASSWORD` of at least 12 characters in `.env.local`.
3. Generate the JWT signing key locally:

   ```powershell
   uv run python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

4. Put the generated value in `JWT_SECRET_KEY` in `.env.local`. Keep it
   private. `.env.local` is ignored by Git; do not commit secrets. In
   production, use the platform's secret manager instead of an env file.
5. Start the server. It validates the required auth settings at startup.
6. Request a token:

   ```http
   POST /network/auth/login
   Content-Type: application/json
   ```

   ```json
   {
     "username": "your-configured-username",
     "password": "your-configured-password"
   }
   ```

   The response contains a bearer JWT valid for 30 minutes:

   ```json
   {
     "access_token": "<signed-jwt>",
     "token_type": "bearer",
     "expires_in": 1800
   }
   ```

7. Send `Authorization: Bearer <access_token>` when creating nodes or edges.
   The read-only node-list and shortest-route endpoints remain public. Invalid
   or expired tokens receive HTTP `401`.

The login endpoint allows five requests per client IP in each 60-second
window. Further requests receive HTTP `429` and a `Retry-After` header. This
limiter is in-process, so its counts are not shared across multiple workers or
application replicas and reset when the process restarts. For those deployment
setups, use a shared store such as Redis. When running behind a reverse proxy,
configure trusted proxy handling before relying on client IP rate limits; do
not trust arbitrary client-supplied forwarding headers.

The configured account is a simple single-user/admin mechanism, not a
multi-user identity system. For production multi-user authentication, use a
user store with hashed passwords or an identity provider.

## Run the application

From the project root:

```powershell
uv run python main.py
```

## Run with Docker

Build the image from the project root:

```powershell
docker build -t server-nodes-app .
```

Run it with the required settings from your local `.env` file:

```powershell
docker run --rm -p 8000:8000 --env-file .env server-nodes-app
```

The `.env` file is not copied into the image. Ensure `DATABASE_URL`,
`AUTH_USERNAME`, `AUTH_PASSWORD`, and `JWT_SECRET_KEY` are set in it. The
database hostname in `DATABASE_URL` must be reachable from the container; for
example, `localhost` inside the container refers to the container itself.

## CORS

The API allows requests from all origins, with `GET` and `POST` methods and
`Authorization` and `Content-Type` headers. Cookie credentials are not enabled;
bearer JWTs are sent using the `Authorization` header. Allowing all origins is
convenient but less restrictive than a production origin allowlist.

## API

### Add a node

`POST /network/nodes`
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
POST /network/edges
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
POST /network/routes/shortest
Content-Type: application/json
Authorization: Bearer <access-token>
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

### Get route query history

```http
POST /network/routes/history
Content-Type: application/json
Authorization: Bearer <access-token>
```

Send a JSON body with the required `limit` and any optional filters:

```json
{
  "limit": 20,
  "date_from": "2026-02-20T00:00:00",
  "date_to": "2026-02-21T00:00:00",
  "source": "ServerA",
  "destination": "ServerD"
}
```

`date_from`, `date_to`, `source`, and `destination` may be omitted. Blank
date or source/destination values are treated as omitted.

This endpoint and `POST /network/routes/shortest` require a valid bearer token.
Each successful shortest-route query is stored in MySQL with its source,
destination, total latency, full path, authenticated username, and IST creation
time. Each authenticated user can only see history rows stored under their
username. Failed route lookups are not stored. History is returned newest first;
`limit` is required and must be between 1 and 100. `source`, `destination`,
`date_from`, and `date_to` are optional; omitting a filter means it does not
restrict the results, so omitting all four returns the authenticated user's
history across all nodes and dates. If supplied, source and destination must
contain at most 100 characters; blank or whitespace-only values are treated as
omitted. Blank or whitespace-only date values are also treated as omitted.
Nonblank dates must be valid ISO 8601 datetimes in IST.
If both dates are supplied, `date_from` must not be later than `date_to`.
Timezone offsets, if present, do not change the supplied wall-clock time. Date
bounds are inclusive. Results are ordered by `created_at` descending.

Each result includes the route's `id`, `source`, `destination`,
`total_latency`, `path`, `username`, and `created_at` with the `+05:30` offset.