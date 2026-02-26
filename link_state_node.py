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
        return "A Generic Node: " + str(self.id) + "\n"
    
    def dijkstra(self, start):
        dist = {start: 0}
        first_hop = {start: -1}

        pq = [(0, start)]
        visited = set()

        while pq:
            current_dist, node = heapq.heappop(pq)
            if node in visited:
                continue
            visited.add(node)

            for neighbor, latency in self.graph.get(node, {}).items():
                if latency == -1:
                    continue
                    
                new_dist = current_dist + latency
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
            del self.graph[self.id][neighbor]
            del self.graph[neighbor][self.id]
            
        else:
            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)
                
                #connect island
                for link, seq in self.links.items():
                    src, dst = tuple(link)
                    if src in self.graph:
                        if dst in self.graph[src]:
                            cost = self.graph[src][dst]
                        else:
                            cost = -1
                    else:
                        cost = -1
                    catch_up_msg = {
                        "source": src,
                        "destination": dst,
                        "cost": cost,
                        "sequence": seq,
                        "sender": self.id
                    }
                    self.send_to_neighbor(neighbor, json.dumps(catch_up_msg))
                
                
            if self.id not in self.graph:
                self.graph[self.id] = {}
            if neighbor not in self.graph:
                self.graph[neighbor] = {}
            self.graph[self.id][neighbor] = latency
            self.graph[neighbor][self.id] = latency

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
            "sequence": self.links[link],
            "sender": self.id
        }
        json_msg = json.dumps(link_msg)
        self.send_to_neighbors(json_msg)
        self.logging.debug('link update, neighbor %d, latency %d, time %d' % (neighbor, latency, self.get_time()))
        


    # Fill in this function
    def process_incoming_routing_message(self, m):
        msg = json.loads(m) 

        source = msg["source"]
        destination = msg["destination"]
        cost = msg["cost"]
        sequence = msg["sequence"]
        sent_from = msg["sender"]

        link = frozenset([source, destination])

        if link not in self.links or sequence > self.links[link]:
            self.links[link] = sequence
            
            if source not in self.graph:
                self.graph[source] = {}
            if destination not in self.graph:
                self.graph[destination] = {}
            
            if cost == -1:
                self.graph[source].pop(destination, None)
                self.graph[destination].pop(source, None)
            else:
                self.graph[source][destination] = cost
                self.graph[destination][source] = cost

        else:
            # old, send back new
            if source in self.graph and destination in self.graph[source]:
                current_cost = self.graph[source][destination]
            else:
                current_cost = -1
            latest_msg = {
                "source": source,
                "destination": destination,
                "cost": current_cost,
                "sequence": self.links[link],
                "sender": self.id
            }
            self.send_to_neighbor(sent_from, json.dumps(latest_msg))
            return
            
        self.dijkstra(self.id)
        
        msg["sender"] = self.id
        m = json.dumps(msg)

        for neighbor in self.neighbors:
            if neighbor != sent_from:
                self.send_to_neighbor(neighbor, m)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        return self.next_hops.get(destination, -1)
