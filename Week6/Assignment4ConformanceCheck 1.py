import xml.etree.ElementTree as ET
from datetime import datetime
import copy
class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.edges = {}
        self.m = self.c = self.r = 0.0
        self.p = 1.0
    def reset_para(self):
        self.m = self.c = self.r = 0.0
        self.p = 1.0
    def add_place(self, name):
        self.places[name] = 0
        return self

    def add_transition(self, name, id):
        self.transitions[id] = {
            'name': name,
            'inputs': set(),
            'outputs': set()
        }
        return self
    def add_edge(self, source, target):
        if source > 0 > target:
            self.transitions[target]['inputs'].add(source)
        elif source < 0 < target:
            self.transitions[source]['outputs'].add(target)
        return self
    def get_tokens(self, place):
        return self.places[place]
    def is_enabled(self, transition):
        for place in self.transitions[transition]['inputs']:
            if self.places[place] == 0:
                return False
        return True
    def add_marking(self, place):
        self.places[place] += 1
        return self
    def fire_transition(self, transition):
        if self.is_enabled(transition):
            for place in self.transitions[transition]['inputs']:
                self.places[place] -= 1
                self.c += 1
            for place in self.transitions[transition]['outputs']:
                self.places[place] += 1
                self.p += 1
        else:
            for place in self.transitions[transition]['inputs']:
                self.places[place] += 1
                self.m += 1
            for place in self.transitions[transition]['inputs']:
                self.places[place] -= 1
                self.c += 1
            for place in self.transitions[transition]['outputs']:
                self.places[place] += 1
                self.p += 1
        return self
    def transition_name_to_id(self, name):
        for transition_id, transition_data in self.transitions.items():
            if transition_data['name'] == name:
                return transition_id
        return None
def read_from_file(filename):
    log_dict = {}
    tree = ET.parse(filename)
    root = tree.getroot()
    namespace = "{http://www.xes-standard.org/}"
    for trace in root.findall(f"{namespace}trace"):
        case_id = None
        events = []
        for string in trace.findall(f"{namespace}string"):
            if string.attrib.get("key") == "concept:name":
                case_id = string.attrib.get("value")
                break
        if case_id is None:
            continue
        for event in trace.findall(f"{namespace}event"):
            event_data = {}
            for string in event.findall(f"{namespace}string"):
                key = string.attrib.get("key")
                value = string.attrib.get("value")
                if key and value is not None:
                    event_data[key] = value

            for date in event.findall(f"{namespace}date"):
                key = date.attrib.get("key")
                date_value = date.attrib.get("value")
                if key and date_value is not None:
                    try:
                        dt = datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S.%f")
                    except ValueError:
                        try:
                            dt = datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S%z")
                        except ValueError:
                            dt = date_value
                    if isinstance(dt, datetime):
                       event_data[key] = dt.replace(tzinfo=None)
                    else:
                        event_data[key] = dt
            for int_val in event.findall(f"{namespace}int"):
                key = int_val.attrib.get("key")
                value = int_val.attrib.get("value")
                if key and value is not None:
                    try:
                        event_data[key] = int(value)
                    except ValueError:
                        event_data[key] = value
            for float_val in event.findall(f"{namespace}float"):
                key = float_val.attrib.get("key")
                value = float_val.attrib.get("value")
                if key and value is not None:
                    try:
                        event_data[key] = float(value)
                    except ValueError:
                        event_data[key] = value
            events.append(event_data)
        log_dict[case_id] = events
    return log_dict
transitions_unique = set()
def alpha(log_dict):
    follows = {}
    for case_id, events in log_dict.items():
        tasks = [event['concept:name'] for event in events]
        for i in range(len(tasks) - 1):
            source = tasks[i]
            target = tasks[i + 1]
            transitions_unique.add(source)
            transitions_unique.add(target)
            if source not in follows:
                follows[source] = {}
            if target not in follows[source]:
                follows[source][target] = 0
            follows[source][target] += 1
    pn.add_place(1)
    pn.add_marking(1)
    transition_with_id = {}
    for i, transition in enumerate(transitions_unique, start=1):
        t_id = i * -1
        transition_with_id[transition] = t_id
        pn.add_transition(transition,t_id)
    p_id=2
    for source, inter_items in follows.items():
        place = -1
        for target, _ in inter_items.items():
            if pn.transitions[transition_with_id[target]]['inputs']:
                for i in pn.transitions[transition_with_id[target]]['inputs']:
                    place = i
                    continue
            if place <0 :
                place = p_id
                pn.add_place(place)
                p_id += 1
                continue
        for target, _ in inter_items.items():
            pn.add_edge(place, transition_with_id[target])
        pn.add_edge(transition_with_id[source], place)
    for id, details in pn.transitions.items():
        if not details['inputs'] and details['outputs']:
            pn.add_edge(1,id)
        if details['inputs'] and not details['outputs']:
            pn.add_place(p_id)
            pn.add_edge(id,p_id)
            p_id+= 1
    return pn
def get_value_k(log):
    traces = set()
    trac_with_n = {}
    for case_id, events in log.items():
        trace = []
        for event in events:
            if 'concept:name' in event:
                trace.append(event['concept:name'])
        traces.add(tuple(trace))
    for i in traces:
        n =0
        for case_id, events in log.items():
            trace = []
            for event in events:
                if 'concept:name' in event:
                    trace.append(event['concept:name'])
            if tuple(trace) == i:
                n += 1
        trac_with_n[i] = n
    return trac_with_n,traces
pn = PetriNet()
def fitness_token_replay(log, mined_model):
    last_events = log[next(iter(log))][-1]['concept:name']
    n =[]
    m =[]
    c =[]
    r =[]
    p =[]
    trac_with_n, traces = get_value_k(log)
    for trace in traces:
        pn.n = trac_with_n[trace]
        pn.reset_para()
        m_places = copy.deepcopy(pn.places)
        for a in trace:
            if a in transitions_unique:
                mined_model.fire_transition(mined_model.transition_name_to_id(a))
        last_events_id = mined_model.transition_name_to_id(last_events)
        for place in pn.transitions[last_events_id]['outputs']:
            if pn.places[place] == 0:
                pn.places[place] += 1
                pn.m += 1
        for place in pn.transitions[last_events_id]['outputs']:
            pn.places[place] -= 1
            pn.c += 1
        for i in pn.places.keys():
            pn.r += pn.places[i]
        n.append(pn.n)
        m.append(pn.m)
        c.append(pn.c)
        r.append(pn.r)
        p.append(pn.p)
        pn.places = copy.deepcopy(m_places)
    conformance = calculate_f(n,m,c,r,p)
    return conformance
def calculate_f(ni, mi, ci, ri, pi):
    # Calculate the numerator and denominator for the first term
    numerator1 = sum(ni[i] * mi[i] for i in range(len(ni)))
    denominator1 = sum(ni[i] * ci[i] for i in range(len(ni)))

    # Calculate the numerator and denominator for the second term
    numerator2 = sum(ni[i] * ri[i] for i in range(len(ni)))
    denominator2 = sum(ni[i] * pi[i] for i in range(len(ni)))

    # Calculate the f value
    f = 0.5 * (1 - numerator1 / denominator1) + 0.5 * (1 - numerator2 / denominator2)

    return f


if __name__ == "__main__":
    log = read_from_file("extension-log-4.xes")
    log_noisy = read_from_file("extension-log-noisy-4.xes")
    mined_model = alpha(log)
    print(round(fitness_token_replay(log, mined_model), 5))
    print(round(fitness_token_replay(log_noisy, mined_model), 5))