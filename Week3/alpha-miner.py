import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict

# Function to log messages to a file
def log_to_file(message):
    with open("log.txt", "a") as log_file:
        log_file.write(message + "\n")

class PetriNet():
    def __init__(self):
        self.places = set()
        self.transitions = set()
        self.tokens = {}
        self.input_arcs = defaultdict(set)   # Place -> Transitions
        self.output_arcs = defaultdict(set)  # Transition -> Places
    
    def add_place(self, name):
        self.places.add(name)
        self.tokens[name] = 0
        return self
    
    def add_transition(self, name):
        self.transitions.add(name)
        return self
    
    def add_input_arc(self, place, transition):
        self.input_arcs[transition].add(place)
        return self
    
    def add_output_arc(self, transition, place):
        self.output_arcs[transition].add(place)
        return self
    
    def add_marking(self, place):
        if place in self.tokens:
            self.tokens[place] += 1
        return self
    
    def is_enabled(self, transition):
        return all(self.tokens.get(place, 0) > 0 for place in self.input_arcs[transition])
    
    def fire_transition(self, transition):
        if self.is_enabled(transition):
            for place in self.input_arcs[transition]:
                self.tokens[place] -= 1
            for place in self.output_arcs[transition]:
                self.tokens[place] += 1
        else:
            print(f"Transition {transition} is not enabled.")
        return self



    def transition_name_to_id(self, name):
        # Find the transition ID based on the transition name
        for id, names in self.transitions.items():
            if name in names:
                return id
        return None

# Alpha Miner Algorithm implementation
def alpha(filename):
    # Read the log
    log = read_from_file(filename)
    
    # Extract unique activities
    activities = set()
    for trace in log.values():
        for event in trace:
            activities.add(event["concept:name"])
    activities = sorted(activities)
    
    # Determine start and end activities
    start_activities = set()
    end_activities = set()
    for trace in log.values():
        if trace:
            start_activities.add(trace[0]["concept:name"])
            end_activities.add(trace[-1]["concept:name"])
    
    # Build directly-follows relations
    directly_follows = set()
    for trace in log.values():
        for i in range(len(trace) - 1):
            a = trace[i]["concept:name"]
            b = trace[i+1]["concept:name"]
            directly_follows.add((a, b))
    
    # Build causal relations
    causal_relations = set()
    for (a, b) in directly_follows:
        if (b, a) not in directly_follows:
            causal_relations.add((a, b))
    
    # Build the Petri net
    pn = PetriNet()
    for activity in activities:
        pn.add_transition(activity)
    
    # Create places
    for (a, b) in causal_relations:
        place_name = f"p_{a}_{b}"
        pn.add_place(place_name)
        pn.add_input_arc(place_name, b)
        pn.add_output_arc(a, place_name)
    
    # Add start and end places
    pn.add_place("start")
    for s in start_activities:
        pn.add_output_arc("start", s)
    pn.add_marking("start")
    
    pn.add_place("end")
    for e in end_activities:
        pn.add_input_arc("end", e)
    
    return pn

# Log file reader
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

def check_enabled(pn):
    ts = ["record issue", "inspection", "intervention authorization", "action not required",
          "work mandate", "no concession", "work completion", "issue completion"]
    for t in ts:
        is_enabled = pn.is_enabled(t)
        print(f"{t}: {is_enabled}")
    print("")


# Read the log and construct the Petri net
mined_model = alpha('extension-log.xes')

# Simulate firing the transitions as per the trace
trace = ["record issue", "inspection", "intervention authorization", "work mandate",
         "work completion", "issue completion"]

for a in trace:
    check_enabled(mined_model)
    mined_model.fire_transition(a)
