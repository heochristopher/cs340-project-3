from simulator.node import Node
import copy
import json

class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.dv = {self.id: {"cost": 0, "path": [self.id]}}
        self.dv_seq = 0
        self.next_hops = {}
        self.neighbor_dvs = {}
        self.neighbor_costs = {}
        self.neighbor_latest_seq = {}

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"
    
    def bellman_ford(self):
        new_dv = {self.id: {"cost": 0, "path": [self.id]}}
        new_next = {}

        dests = set(self.dv.keys())

        for dv in self.neighbor_dvs.values():
            dests.update(dv.keys())

        for dest in dests:
            if dest == self.id:
                continue

            min_cost = float('inf')
            min_path = None
            min_hop = None

            for neighbor, cost in self.neighbor_costs.items():
                if cost == -1:
                    continue
                neighbor_dv = self.neighbor_dvs.get(neighbor, {})
                data = neighbor_dv.get(dest)
                if data is None:
                    continue
                
                cost_to_dest = data.get("cost", float('inf'))
                path_to_dest = data.get("path", [])

                if cost_to_dest == float('inf'):
                    continue

                if self.id in path_to_dest:
                    continue

                total_cost = cost + cost_to_dest
                if total_cost < min_cost:
                    min_cost = total_cost
                    min_path = [self.id] + path_to_dest
                    min_hop = neighbor
            
            if min_cost < float('inf') and min_path is not None and min_hop is not None:
                new_dv[dest] = {"cost": min_cost, "path": min_path}
                new_next[dest] = min_hop
        
        changed = (new_dv != self.dv) or (new_next != self.next_hops)
        self.dv = new_dv
        self.next_hops = new_next
        return changed

    def send_updates(self):
        self.dv_seq += 1
        
        for neighbor in self.neighbors:
            vector = {}

            for dest, data in self.dv.items():
                cost = data["cost"]
                path = data["path"]

                if dest != self.id and self.next_hops.get(dest) == neighbor:
                    vector[str(dest)] = {"cost": float('inf'), "path": [self.id]}
                else:
                    vector[str(dest)] = {"cost": int(cost), "path": copy.deepcopy(path) }
            
            message = {"sender": self.id, "seq": self.dv_seq, "vector": vector}
            self.send_to_neighbor(neighbor, json.dumps(message))

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link
        if latency == -1:
            if neighbor in self.neighbors:
                self.neighbors.remove(neighbor)
            del self.neighbor_costs[neighbor]
            del self.neighbor_dvs[neighbor]
            del self.neighbor_latest_seq[neighbor]
            was_updated = self.bellman_ford()
            if was_updated:
                self.send_updates()
        else:
            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)
            self.neighbor_costs[neighbor] = latency
            if neighbor not in self.neighbor_dvs:
                self.neighbor_dvs[neighbor] = {neighbor: {"cost": 0, "path": [neighbor]}}
            
            was_updated = self.bellman_ford()
            if was_updated:
                self.send_updates()

    # Fill in this function
    def process_incoming_routing_message(self, m):
        message = json.loads(m)
        sender = message["sender"]
        seq = message["seq"]
        vector = message["vector"]

        if seq <= self.neighbor_latest_seq.get(sender, -1):
            return
        
        self.neighbor_latest_seq[sender] = seq
        dv = {}

        for dest_str, data in vector.items():
            dest = int(dest_str)
            cost = data.get("cost", float('inf'))
            path = data.get("path", [])

            if isinstance(path, list):
                path = [int(x) for x in path]
            else:
                path = []
            
            dv[dest] = {"cost": cost, "path": path}

        self.neighbor_dvs[sender] = dv
        was_updated = self.bellman_ford()
        if was_updated:
            self.send_updates()
            
    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        return self.next_hops.get(destination, -1)