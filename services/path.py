import heapq
import math

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from utils.validation import (
    PathLookupRequest,
    PathLookupResponse,
    PathNotFoundResponse,
)


async def find_path(
    conn: AsyncConnection,
    payload: PathLookupRequest,
) -> PathLookupResponse | PathNotFoundResponse:
    """Return the minimum-latency route between two nodes.

    Dijkstra's algorithm is used because edge latencies can differ: the route
    with the fewest edges is not necessarily the route with the least latency.
    Since valid edge latencies are positive, processing routes in increasing
    total-latency order guarantees that the first finalized route is shortest.
    """
    source = payload.source.strip()
    destination = payload.destination.strip()
    # Reuse one response when either endpoint is unknown or no route connects them.
    no_path = PathNotFoundResponse(
        error=f"No path exists between {source} and {destination}"
    )

    nodes_result = await conn.execute(text("SELECT name FROM nodes"))
    # A set makes checking that both requested endpoints exist efficient.
    node_names = {row.name for row in nodes_result}
    if source not in node_names or destination not in node_names:
        return no_path

    edges_result = await conn.execute(
        text("SELECT source_name, destination_name, latency FROM edges")
    )
    # Map each node to its neighbors. Add both directions because edges are undirected.
    adjacency: dict[str, list[tuple[str, float]]] = {name: [] for name in node_names}
    for edge in edges_result:
        latency = float(edge.latency)
        adjacency[edge.source_name].append((edge.destination_name, latency))
        adjacency[edge.destination_name].append((edge.source_name, latency))

    # Best total latency found so far from source to each node.
    distances = {source: 0.0}
    # Previous node on each best-known route; used later to rebuild the path.
    previous: dict[str, str] = {}
    # Min-heap of (total latency so far, node); it selects the cheapest route to explore.
    queue = [(0.0, source)]

    # Explore candidate routes from lowest latency to highest until the destination
    # is finalized or there are no reachable nodes left.
    while queue:
        current_distance, current = heapq.heappop(queue)
        # A better route may have been found after this entry was added to the heap.
        if current_distance != distances.get(current):
            continue
        # With positive edge weights, this is now the minimum-latency route to destination.
        if current == destination:
            break

        # Check each directly connected neighbor to see whether going through
        # current gives it a lower total latency than any route found so far.
        for neighbor, latency in adjacency[current]:
            candidate_distance = current_distance + latency
            if candidate_distance < distances.get(neighbor, math.inf):
                distances[neighbor] = candidate_distance
                previous[neighbor] = current
                heapq.heappush(queue, (candidate_distance, neighbor))

    if destination not in distances:
        return no_path

    # Walk backward through the recorded predecessors, then reverse to return
    # the route in the requested source-to-destination order.
    path = [destination]
    while path[-1] != source:
        path.append(previous[path[-1]])
    path.reverse()

    return PathLookupResponse(
        total_latency=distances[destination],
        path=path,
    )
