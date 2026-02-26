import json
from simulator.node import Node
import heapq

class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.graph = {}
        self.next_hops = {}
        self.links = {}

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"
    
    def dijkstra(self, start):
        dist = {start: 0}
        first_hop = {start: -1}

        pq = [(0, start)]
        visited = set()

        while pq:
            dist, node = heapq.heappop(pq)
            if node in visited:
                continue
            visited.add(node)

            for neighbor, latency in self.graph.get(node, {}).items():
                if latency == -1:
                    continue
                    
                new_dist = dist + latency
                if new_dist < dist.get(neighbor, float('inf')):
                    dist[neighbor] = new_dist
                    if node == start:
                        first_hop[neighbor] = neighbor
                    else:
                        first_hop[neighbor] = first_hop[node]
                    
                    heapq.heappush(pq, (new_dist, neighbor))

        first_hop.pop(start, None)
        self.next_hops = first_hop
        return dist

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1 and neighbor in self.neighbors:
            self.neighbors.remove(neighbor)
            del self.graph[neighbor]
            del self.graph[self.id][neighbor]
        else:
            self.neighbors.append(neighbor)
            self.graph[neighbor] = latency
            self.graph[self.id][neighbor] = latency

        link = frozenset({self.id, neighbor})
        if link not in self.links:
            self.links[link] = 0
        else:
            self.links[link] += 1

        self.dijkstra(self.id)

        link_msg = {
            "source": self.id,
            "destination": neighbor,
            "cost": latency,
            "sequence": self.links[link]
        }
        json_msg = json.dumps(link_msg)
        self.send_to_neighbors(json_msg)
        self.logging.debug('link update, neighbor %d, latency %d, time %d' % (neighbor, latency, self.get_time()))
        
        pass

    # Fill in this function
    def process_incoming_routing_message(self, m):
        msg = json.loads(m) 

        source = msg["source"]
        destination = msg["destination"]
        cost = msg["cost"]
        sequence = msg["sequence"]

        link = frozenset([source, destination])

        if link not in self.links:
            self.links[link] = sequence
        else:
            if sequence > self.links[link]:
                self.links[link] = sequence
            else:
                # Old, dont propogate
                latest_msg = {
                    "source": source,
                    "destination": destination,
                    "cost": self.graph[source][destination],
                    "sequence": self.links[link]["sequence"]
                }
                json_latest = json.dumps(latest_msg)
                if sender_id is not None:
                    self.send_to_neighbor(sender_id, json_latest)
                return
        self.dijkstra(self.id)

        for neighbor in self.neighbors:
            if neighbor != sender_id:
                self.send_to_neighbor(neighbor, m)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        return self.next_hops.get(destination, -1)
