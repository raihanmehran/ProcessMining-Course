import datetime
import xml.etree.ElementTree as ET
import itertools
from collections import defaultdict

class PetriNet():
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.input_edges = {}
        self.output_edges = {}
        self.name_to_id = {}

    def add_place(self, name):
        if name not in self.places:
            self.places[name] = 0
        return self

    def add_transition(self, name, transition_id):
        if transition_id not in self.transitions:
            self.transitions[transition_id] = name
            self.name_to_id[name] = transition_id
        return self

    def add_edge(self, source, target):
        if source in self.places and target in self.transitions:
            if target not in self.input_edges:
                self.input_edges[target] = []
            self.input_edges[target].append(source)
        elif source in self.transitions and target in self.places:
            if source not in self.output_edges:
                self.output_edges[source] = []
            self.output_edges[source].append(target)
        return self

    def get_tokens(self, place):
        return self.places.get(place, 0)

    def is_enabled(self, transition):
        if transition not in self.input_edges:
            return False
        for place in self.input_edges[transition]:
            if self.places[place] < 1:
                return False
        return True

    def add_marking(self, place):
        if place in self.places:
            self.places[place] += 1
        return self

    def fire_transition(self, transition):
        if self.is_enabled(transition):
            for place in self.input_edges[transition]:
                self.places[place] -= 1
            for place in self.output_edges.get(transition, []):
                self.places[place] += 1
        else:
            print(f"Transition {self.transitions[transition]} is not enabled.")
        return self

    def transition_name_to_id(self, name):
        return self.name_to_id.get(name, None)

def build_dependency_graph(log):
    dependency_graph = {}

    for case, events in log.items():
        for idx in range(len(events) - 1):
            current_task = events[idx]['concept:name']
            next_task = events[idx + 1]['concept:name']

            if current_task not in dependency_graph:
                dependency_graph[current_task] = {}

            if next_task not in dependency_graph[current_task]:
                dependency_graph[current_task][next_task] = 0

            dependency_graph[current_task][next_task] += 1
    return dependency_graph

def are_pairs_in_set(A, B, target_set):
    for item_A in A:
        for item_B in B:
            if (item_A, item_B) not in target_set:
                return False
    return True

def alpha(log):
    pn = PetriNet()
    transitions = set()

    for trace in log.values():
        for event in trace:
            transitions.add(event['concept:name'])

    initial_transitions = {case_events[0]['concept:name'] for case_events in log.values()}
    final_transitions = {case_events[-1]['concept:name'] for case_events in log.values()}

    dependency_graph = build_dependency_graph(log)

    directly_follows = set()
    causalities = set()
    parallel_relations = set()
    choice_relations = set()

    for transition_1 in sorted(dependency_graph.keys()):
        for transition_2 in sorted(dependency_graph[transition_1].keys()):
            directly_follows.add((transition_1, transition_2))

    for t1 in transitions:
        for t2 in transitions:
            if (t1, t2) not in directly_follows and (t2, t1) not in directly_follows:
                choice_relations.add((t1, t2))

    for (source, target) in directly_follows:
        if (target, source) not in directly_follows:
            causalities.add((source, target))
        else:
            parallel_relations.add((source, target))

    candidate_pairs = set()
    subsets = set()

    for size in range(1, len(transitions) + 1):
        for subset in itertools.combinations(transitions, size):
            subsets.add(subset)

    for subset_1 in subsets:
        if are_pairs_in_set(subset_1, subset_1, choice_relations):
            for subset_2 in subsets:
                if are_pairs_in_set(subset_2, subset_2, choice_relations):
                    if are_pairs_in_set(subset_1, subset_2, causalities):
                        candidate_pairs.add((subset_1, subset_2))

    maximal_pairs = candidate_pairs.copy()
    for pair in candidate_pairs:
        set_a = set(pair[0])
        set_b = set(pair[1])
        for other_pair in candidate_pairs:
            if set_a.issubset(other_pair[0]) and set_b.issubset(other_pair[1]):
                if pair != other_pair:
                    maximal_pairs.discard(pair)

    for transition in transitions:
        pn.add_transition(transition, f"{transition}")

    pn.add_place('start')
    pn.add_marking('start')
    for activity in initial_transitions:
        pn.add_edge('start', pn.transition_name_to_id(activity))

    pn.add_place('end')
    for activity in final_transitions:
        pn.add_edge(pn.transition_name_to_id(activity), 'end')

    for i, (pre_set, post_set) in enumerate(maximal_pairs):
        place_name = f'p{i}'
        pn.add_place(place_name)
        for event in pre_set:
            pn.add_edge(pn.transition_name_to_id(event), place_name)
        for event in post_set:
            pn.add_edge(place_name, pn.transition_name_to_id(event))

    return pn

def read_from_file(filename):
    xes = {'xes': 'http://www.xes-standard.org/'}
    tree = ET.parse(filename)
    root = tree.getroot()
    cases = {}
    for trace in root.findall('xes:trace', xes):
        case_id_element = trace.find('xes:string[@key="concept:name"]', xes)
        if case_id_element is not None:
            case_id = case_id_element.attrib['value']
        else:
            case_id = str(len(cases) + 1)
        events = []
        for event in trace.findall('xes:event', xes):
            event_dict = {}
            for element in event:
                key = element.attrib['key']
                value = element.attrib['value']

                if key == 'time:timestamp':
                    try:
                        date = datetime.datetime.fromisoformat(value)
                    except ValueError:
                        date = datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S%z")
                    date_no_tz = date.replace(tzinfo=None)
                    event_dict[key] = date_no_tz
                elif key == 'cost':
                    event_dict['cost'] = int(value)
                else:
                    event_dict[key] = value
            events.append(event_dict)

        cases[case_id] = events
    return cases

def fitness_token_replay(log, model):
    total_produced = 0
    total_consumed = 0
    total_missing = 0
    total_remaining = 0

    for case_id, trace in log.items():
        # Reset the marking on the model for each trace replay
        model.places = {place: 0 for place in model.places}  # Reset all places to 0
        model.places['start'] = 1  # Place token in 'start' place (provided by environment)

        produced = 0  # Tokens produced by transitions
        consumed = 0  # Tokens consumed by transitions
        missing = 0   # Missing tokens required for transitions

        for event in trace:
            transition_name = event['concept:name']
            transition_id = model.transition_name_to_id(transition_name)

            if transition_id is None:
                continue  # Skip if transition name is not in the model

            input_places = model.input_edges.get(transition_id, [])
            output_places = model.output_edges.get(transition_id, [])

            if model.is_enabled(transition_id):
                # Consume tokens from input places
                for place in input_places:
                    model.places[place] -= 1
                    consumed += 1  # Count tokens consumed by transitions

                # Produce tokens to output places
                for place in output_places:
                    model.places[place] += 1
                    produced += 1  # Count tokens produced by transitions

            else:
                # Transition is not enabled; count missing tokens
                for place in input_places:
                    required_tokens = 1  # Assuming arc weight is 1
                    available_tokens = model.get_tokens(place)
                    if available_tokens < required_tokens:
                        missing += (required_tokens - available_tokens)

        # Remaining tokens in places (excluding 'end' place)
        remaining = sum(
            tokens for place, tokens in model.places.items()
            if place != 'end' and tokens > 0
        )

        # Accumulate totals
        total_produced += produced
        total_consumed += consumed
        total_missing += missing
        total_remaining += remaining

    # Compute fitness using the correct formula
    if (total_consumed + total_missing) > 0:
        fitness_consumed = 1 - (total_missing / (total_consumed + total_missing))
    else:
        fitness_consumed = 1.0

    if (total_produced + total_remaining) > 0:
        fitness_produced = 1 - (total_remaining / (total_produced + total_remaining))
    else:
        fitness_produced = 1.0

    fitness = 0.5 * (fitness_consumed + fitness_produced)

    # Clamp the fitness value between 0 and 1
    fitness = max(0.0, min(fitness, 1.0))

    return fitness


# Example usage:
log = read_from_file("extension-log-4.xes")
log_noisy = read_from_file("extension-log-noisy-4.xes")

mined_model = alpha(log)
print("Fitness for clean log:", round(fitness_token_replay(log, mined_model), 5))
print("Fitness for noisy log:", round(fitness_token_replay(log_noisy, mined_model), 5))
