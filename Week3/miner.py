import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict

class PetriNet():
    def __init__(self):
        self.places = []
        self.transitions = {}
        self.edges = {}
        self.tokens = {}
        self.markings = {}
        self.is_enabled_dict = {}
        self.fired_transition = {}
        self.name_to_id = {}

    def add_place(self, name):
        if name not in self.places:
            self.places.append(name)
            self.tokens[name] = 0
            self.markings[name] = 0
        return self

    def add_transition(self, name, id):
        if id not in self.transitions:
            self.transitions[id] = []
        if name not in self.transitions[id]:
            self.transitions[id].append(name)
        self.name_to_id[name] = id
        return self

    def add_edge(self, source, target):
        if source not in self.edges:
            self.edges[source] = []
        if target not in self.edges[source]:
            self.edges[source].append(target)
        return self

    def get_tokens(self, place):
        return self.tokens.get(place, 0)

    def is_enabled(self, transition):
        incoming_places = [place for place in self.edges if transition in self.edges[place]]
        for place in incoming_places:
            if self.tokens.get(place, 0) <= 0:
                self.is_enabled_dict[transition] = False
                return False
        self.is_enabled_dict[transition] = True
        return True

    def add_marking(self, place):
        if place in self.tokens:
            self.tokens[place] += 1
        return self

    def fire_transition(self, transition):
        if self.is_enabled(transition):
            incoming_places = [place for place in self.edges if transition in self.edges[place]]
            outgoing_places = self.edges.get(transition, [])
            for place in incoming_places:
                self.tokens[place] -= 1
            for place in outgoing_places:
                self.tokens[place] += 1
            self.fired_transition[transition] = True
        else:
            print(f"Transition {transition} is not enabled.")
        return self

    def transition_name_to_id(self, name):
        return self.name_to_id.get(name, None)

def alpha(log):
    T_L = set()
    for trace in log.values():
        for event in trace:
            T_L.add(event["concept:name"])
    
    W_L = set()
    for trace in log.values():
        events = trace
        for i in range(len(events) - 1):
            a = events[i]["concept:name"]
            b = events[i + 1]["concept:name"]
            W_L.add((a, b))
    
    causal_relations = set()
    parallel_relations = set()
    for (a, b) in W_L:
        if (b, a) not in W_L:
            causal_relations.add((a, b))
        elif (b, a) in W_L and (a, b) in W_L:
            parallel_relations.add((a, b))
            parallel_relations.add((b, a))
            
    successor_map = {task: set() for task in T_L}
    predecessor_map = {task: set() for task in T_L}
    for (a, b) in W_L:
        successor_map[a].add(b)
        predecessor_map[b].add(a)
    
    initial_tasks = set()
    final_tasks = set()
    for trace in log.values():
        if trace:
            initial_tasks.add(trace[0]["concept:name"])
            final_tasks.add(trace[-1]["concept:name"])
    
    pn = PetriNet()
    
    pn.add_place('start')
    pn.add_place('end')
    
    for task in T_L:
        pn.add_transition(task, task) 
    
    for task in initial_tasks:
        pn.add_edge('start', task)
    for task in final_tasks:
        pn.add_edge(task, 'end')
    
    pn.tokens['start'] = 1
    
    places_set = set()
    for t in T_L:
        if len(predecessor_map[t]) > 0:
            inputs = tuple(sorted(predecessor_map[t]))
            outputs = (t,)
            place = (inputs, outputs)
            places_set.add(place)

        if len(successor_map[t]) > 0:
            inputs = (t,)
            outputs = tuple(sorted(successor_map[t]))
            place = (inputs, outputs)
            places_set.add(place)
    
    place_counter = 0
    for (inputs, outputs) in places_set:
        place_name = f'p{place_counter}'
        place_counter += 1
        pn.add_place(place_name)
        for input_t in inputs:
            pn.add_edge(input_t, place_name)
        for output_t in outputs:
            pn.add_edge(place_name, output_t)
    
    return pn

def read_from_file(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    namespace = {'xes': 'http://www.xes-standard.org/'}
    log_dict = defaultdict(list)

    for trace in root.findall('xes:trace', namespace):
        case_id = None
        for trace_attr in trace.findall('xes:string', namespace):
            if trace_attr.get('key') == 'concept:name':
                case_id = trace_attr.get('value')
                break
        
        if case_id is None:
            continue

        for event in trace.findall('xes:event', namespace):
            event_data = {
                "concept:name": "record issue",  
                "org:resource": "admin-1",       
                "time:timestamp": datetime.datetime(1970, 1, 1, 1, 0),  
                "cost": 11                      
            }
            
            for attr in event:
                key = attr.get('key')
                if key == "concept:name":
                    event_data["concept:name"] = attr.get('value', 'record issue')
                elif key == "org:resource":
                    event_data["org:resource"] = attr.get('value', 'admin-1')
                elif key == "time:timestamp":
                    timestamp_value = attr.get('value', None)
                    try:
                        event_data["time:timestamp"] = datetime.datetime.strptime(timestamp_value, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=None)
                    except ValueError:
                        try:
                            event_data["time:timestamp"] = datetime.datetime.strptime(timestamp_value, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                        except ValueError:
                            event_data["time:timestamp"] = datetime.datetime(1970, 1, 1, 1, 0)
                elif key == "cost":
                    try:
                        cost_value = float(attr.get('value', 0))
                        event_data["cost"] = int(cost_value) if cost_value.is_integer() else cost_value
                    except (ValueError, TypeError):
                        event_data["cost"] = 11

            log_dict[case_id].append(event_data)

    return log_dict
