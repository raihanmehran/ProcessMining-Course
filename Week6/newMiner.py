import xml.etree.ElementTree as ElemTree
from datetime import datetime
import copy

class PetriNet:
    def __init__(self):
        self.places_dict = {}
        self.transitions_dict = {}
        self.edges_dict = {}
        self.missing_tokens = self.consumed_tokens = self.remaining_tokens = 0.0
        self.produced_tokens = 1.0

    def reset_metrics(self):
        self.missing_tokens = self.consumed_tokens = self.remaining_tokens = 0.0
        self.produced_tokens = 1.0

    def add_place(self, place_name):
        self.places_dict[place_name] = 0
        return self

    def add_transition(self, transition_name, transition_id):
        self.transitions_dict[transition_id] = {
            'name': transition_name,
            'inputs': set(),
            'outputs': set()
        }
        return self

    def add_edge(self, source, target):
        if source > 0 > target:
            self.transitions_dict[target]['inputs'].add(source)
        elif source < 0 < target:
            self.transitions_dict[source]['outputs'].add(target)
        return self

    def get_token_count(self, place):
        return self.places_dict[place]

    def is_transition_enabled(self, transition_id):
        for place in self.transitions_dict[transition_id]['inputs']:
            if self.places_dict[place] == 0:
                return False
        return True

    def add_marking(self, place):
        self.places_dict[place] += 1
        return self

    def fire_transition(self, transition_id):
        if self.is_transition_enabled(transition_id):
            for place in self.transitions_dict[transition_id]['inputs']:
                self.places_dict[place] -= 1
                self.consumed_tokens += 1
            for place in self.transitions_dict[transition_id]['outputs']:
                self.places_dict[place] += 1
                self.produced_tokens += 1
        else:
            for place in self.transitions_dict[transition_id]['inputs']:
                self.places_dict[place] += 1
                self.missing_tokens += 1
            for place in self.transitions_dict[transition_id]['inputs']:
                self.places_dict[place] -= 1
                self.consumed_tokens += 1
            for place in self.transitions_dict[transition_id]['outputs']:
                self.places_dict[place] += 1
                self.produced_tokens += 1
        return self

    def get_transition_id_by_name(self, transition_name):
        for trans_id, trans_data in self.transitions_dict.items():
            if trans_data['name'] == transition_name:
                return trans_id
        return None

def read_from_file(file_name):
    log_data = {}
    xml_tree = ElemTree.parse(file_name)
    xml_root = xml_tree.getroot()
    namespace = "{http://www.xes-standard.org/}"
    for trace in xml_root.findall(f"{namespace}trace"):
        case_id = None
        events = []
        for elem in trace.findall(f"{namespace}string"):
            if elem.attrib.get("key") == "concept:name":
                case_id = elem.attrib.get("value")
                break
        if case_id is None:
            continue
        for event in trace.findall(f"{namespace}event"):
            event_details = {}
            for elem in event.findall(f"{namespace}string"):
                key = elem.attrib.get("key")
                value = elem.attrib.get("value")
                if key and value is not None:
                    event_details[key] = value
            for elem in event.findall(f"{namespace}date"):
                key = elem.attrib.get("key")
                date_value = elem.attrib.get("value")
                if key and date_value is not None:
                    try:
                        dt = datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S.%f")
                    except ValueError:
                        try:
                            dt = datetime.strptime(date_value, "%Y-%m-%dT%H:%M:%S%z")
                        except ValueError:
                            dt = date_value
                    if isinstance(dt, datetime):
                       event_details[key] = dt.replace(tzinfo=None)
                    else:
                        event_details[key] = dt
            for elem in event.findall(f"{namespace}int"):
                key = elem.attrib.get("key")
                value = elem.attrib.get("value")
                if key and value is not None:
                    try:
                        event_details[key] = int(value)
                    except ValueError:
                        event_details[key] = value
            for elem in event.findall(f"{namespace}float"):
                key = elem.attrib.get("key")
                value = elem.attrib.get("value")
                if key and value is not None:
                    try:
                        event_details[key] = float(value)
                    except ValueError:
                        event_details[key] = value
            events.append(event_details)
        log_data[case_id] = events
    return log_data

unique_transitions_set = set()

def alpha(log_data):
    follow_relations = {}
    for case_id, events in log_data.items():
        tasks_sequence = [event['concept:name'] for event in events]
        for i in range(len(tasks_sequence) - 1):
            source = tasks_sequence[i]
            target = tasks_sequence[i + 1]
            unique_transitions_set.add(source)
            unique_transitions_set.add(target)
            if source not in follow_relations:
                follow_relations[source] = {}
            if target not in follow_relations[source]:
                follow_relations[source][target] = 0
            follow_relations[source][target] += 1

    petri_net.add_place(1)
    petri_net.add_marking(1)
    transition_id_map = {}
    for i, transition in enumerate(unique_transitions_set, start=1):
        trans_id = i * -1
        transition_id_map[transition] = trans_id
        petri_net.add_transition(transition, trans_id)

    place_id = 2
    for source, target_relations in follow_relations.items():
        current_place = -1
        for target, _ in target_relations.items():
            if petri_net.transitions_dict[transition_id_map[target]]['inputs']:
                for place in petri_net.transitions_dict[transition_id_map[target]]['inputs']:
                    current_place = place
                    continue
            if current_place < 0:
                current_place = place_id
                petri_net.add_place(current_place)
                place_id += 1
                continue
        for target, _ in target_relations.items():
            petri_net.add_edge(current_place, transition_id_map[target])
        petri_net.add_edge(transition_id_map[source], current_place)

    for trans_id, trans_data in petri_net.transitions_dict.items():
        if not trans_data['inputs'] and trans_data['outputs']:
            petri_net.add_edge(1, trans_id)
        if trans_data['inputs'] and not trans_data['outputs']:
            petri_net.add_place(place_id)
            petri_net.add_edge(trans_id, place_id)
            place_id += 1

    return petri_net

def extract_trace_data(log):
    unique_traces = set()
    trace_counts = {}
    for case_id, events in log.items():
        trace_sequence = []
        for event in events:
            if 'concept:name' in event:
                trace_sequence.append(event['concept:name'])
        unique_traces.add(tuple(trace_sequence))
    for trace in unique_traces:
        count = 0
        for case_id, events in log.items():
            trace_sequence = []
            for event in events:
                if 'concept:name' in event:
                    trace_sequence.append(event['concept:name'])
            if tuple(trace_sequence) == trace:
                count += 1
        trace_counts[trace] = count
    return trace_counts, unique_traces

petri_net = PetriNet()

def fitness_token_replay(log, mined_model):
    final_event = log[next(iter(log))][-1]['concept:name']
    trace_frequencies = []
    missing_counts = []
    consumed_counts = []
    remaining_counts = []
    produced_counts = []
    trace_counts, unique_traces = extract_trace_data(log)
    for trace in unique_traces:
        petri_net.n_val = trace_counts[trace]
        petri_net.reset_metrics()
        initial_places = copy.deepcopy(petri_net.places_dict)
        for task in trace:
            if task in unique_transitions_set:
                mined_model.fire_transition(mined_model.get_transition_id_by_name(task))
        final_event_id = mined_model.get_transition_id_by_name(final_event)
        for place in petri_net.transitions_dict[final_event_id]['outputs']:
            if petri_net.places_dict[place] == 0:
                petri_net.places_dict[place] += 1
                petri_net.missing_tokens += 1
        for place in petri_net.transitions_dict[final_event_id]['outputs']:
            petri_net.places_dict[place] -= 1
            petri_net.consumed_tokens += 1
        for place in petri_net.places_dict.keys():
            petri_net.remaining_tokens += petri_net.places_dict[place]
        trace_frequencies.append(petri_net.n_val)
        missing_counts.append(petri_net.missing_tokens)
        consumed_counts.append(petri_net.consumed_tokens)
        remaining_counts.append(petri_net.remaining_tokens)
        produced_counts.append(petri_net.produced_tokens)
        petri_net.places_dict = copy.deepcopy(initial_places)

    conformance_score = compute_conformance(trace_frequencies, missing_counts, consumed_counts, remaining_counts, produced_counts)
    return conformance_score

def compute_conformance(frequencies, missing, consumed, remaining, produced):
    numerator1 = sum(frequencies[i] * missing[i] for i in range(len(frequencies)))
    denominator1 = sum(frequencies[i] * consumed[i] for i in range(len(frequencies)))
    numerator2 = sum(frequencies[i] * remaining[i] for i in range(len(frequencies)))
    denominator2 = sum(frequencies[i] * produced[i] for i in range(len(frequencies)))
    return 0.5 * (1 - numerator1 / denominator1) + 0.5 * (1 - numerator2 / denominator2)

if __name__ == "__main__":
    log_standard = read_from_file("extension-log-4.xes")
    log_noisy = read_from_file("extension-log-noisy-4.xes")
    mined_model = alpha(log_standard)
    print(round(fitness_token_replay(log_standard, mined_model), 5))
    print(round(fitness_token_replay(log_noisy, mined_model), 5))
