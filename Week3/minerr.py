import itertools
import xml.etree.ElementTree as ET
from datetime import datetime

class PetriNet:
    def __init__(self):
        self.places = {}
        self.transitions = {}
        self.input_edges = {}
        self.output_edges = {}

    def add_place(self, name):
        self.places[name] = 0

    def add_transition(self, name, transition_id):
        self.transitions[transition_id] = name

    def add_edge(self, source, target):
        if source in self.places and target in self.transitions:
            if target not in self.input_edges:
                self.input_edges[target] = []
            self.input_edges[target].append(source)
        elif source in self.transitions and target in self.places:
            if source not in self.output_edges:
                self.output_edges[source] = []
            if target not in self.output_edges[source]:
                self.output_edges[source].append(target)
        return self

    def get_tokens(self, place):
        return self.places[place]

    def is_enabled(self, transition):
        if transition not in self.input_edges:
            return False
        for place in self.input_edges[transition]:
            if self.places[place] < 1:
                return False
        return True

    def add_marking(self, place):
        self.places[place] += 1

    def fire_transition(self, transition):
        if self.is_enabled(transition):
            for place in self.input_edges[transition]:
                self.places[place] -= 1

            for place in self.output_edges[transition]:
                self.places[place] += 1

    def transition_name_to_id(self, name):
        for t_id, t_name in self.transitions.items():
            if t_name == name:
                return t_id
        return None


def dependency_graph_inline(log):
    dependency_graph = {}

    for case, events in log.items():

        for i in range(len(events) - 1):
            task_1 = events[i]['concept:name']
            task_2 = events[i + 1]['concept:name']

            if task_1 not in dependency_graph:
                dependency_graph[task_1] = {}

            if task_2 not in dependency_graph[task_1]:
                dependency_graph[task_1][task_2] = 0

            dependency_graph[task_1][task_2] += 1
    return dependency_graph


def read_from_file(filename):
    xes = {'xes': 'http://www.xes-standard.org/'}
    tree = ET.parse(filename)
    root = tree.getroot()
    cases = {}
    for trace in root.findall('xes:trace', xes):
        case_id = trace.find('xes:string[@key="concept:name"]', xes).attrib['value']
        events = []
        for event in trace.findall('xes:event', xes):
            event_dict = {}
            for element in event:
                key = element.attrib['key']
                value = element.attrib['value']

                if key == 'time:timestamp':
                    date = datetime.fromisoformat(value)
                    date_no_tz = date.replace(tzinfo=None)
                    event_dict[key] = date_no_tz
                elif key == 'cost':
                    event_dict['cost'] = int(value)
                else:
                    event_dict[key] = value
            events.append(event_dict)

        cases[case_id] = events
    return cases

def check_sets(A, B, set_to_check):
    for activity in A:
        for activity2 in B:
            if (activity, activity2) not in set_to_check:
                return False

    return True

def alpha(log):
    pn = PetriNet()
    transitions = set()

    """Step 1: Find all activities and add them as a transition"""
    for i, trace in enumerate(log.values()):
        for event in trace:
            transition_name = event['concept:name']
            transitions.add(transition_name)

    """Step 2: Find the set of initial transitions and final transitions"""
    initial_transitions = set()
    final_transitions = set()

    for case_events in log.values():
        initial_transitions.add(case_events[0]['concept:name'])
        final_transitions.add(case_events[-1]['concept:name'])

    """ Step 3: Find relations and calculate pairs """
    # Build dependency graph
    dg = dependency_graph_inline(log)

    directly_follows = set()  # A -> B
    causalities = set()  # A -> B and not B -> A
    parallel = set()  # A || B
    choices = set()  # A -> B or A -> C

    for ai in sorted(dg.keys()):
        for aj in sorted(dg[ai].keys()):
            directly_follows.add((ai, aj))

    # Find all unrelated transitions
    for t1 in transitions:
        for t2 in transitions:
            if (t1, t2) not in directly_follows and (t2, t1) not in directly_follows:
                choices.add((t1, t2))

    # Find causal and parallel transitions
    for (x, y) in directly_follows:
        if (y, x) not in directly_follows:
            causalities.add((x, y))
        else:
            parallel.add((x, y))

    xl = set()
    subsets = set()

    for a in range(1, len(transitions)):
        for combination in list(itertools.combinations(transitions, a)):
            subsets.add(combination)

    for combination in subsets:
        if check_sets(combination, combination, choices):
            for combination2 in subsets:
                if check_sets(combination2, combination2, choices):
                    if check_sets(combination, combination2, causalities):
                        xl.add((combination, combination2))

    # Remove all non-maximal pairs
    """ Step 4: Remove all non-maximal pairs """
    yl = xl.copy()
    for x in xl:
        a = set(x[0])
        b = set(x[1])
        for y in xl:
            if a.issubset(y[0]) and b.issubset(y[1]):
                if x != y:
                    yl.discard(x)

    """ Step 5: Create Petri net"""
    # Add transitions
    for t in transitions:
        pn.add_transition(t, f"{t}")

    # Start places
    for activity in initial_transitions:
        pn.add_place('start')
        pn.add_edge('start', pn.transition_name_to_id(activity))
        pn.add_marking('start')

    # End places
    for activity in final_transitions:
        pn.add_place("end")
        pn.add_edge(pn.transition_name_to_id(activity), 'end')

    # Add places and edges
    for i, (a, b) in enumerate(yl):
        place_name = i
        pn.add_place(place_name)
        for e in a:
            pn.add_edge(pn.transition_name_to_id(e), place_name)
        for e in b:
            pn.add_edge(place_name, pn.transition_name_to_id(e))
    return pn



mined_model = alpha(read_from_file("extension-log.xes"))

def check_enabled(pn):
    ts = ["record issue", "inspection", "intervention authorization", "action not required", "work mandate", "no concession", "work completion", "issue completion"]
    for t in ts:
        print(pn.is_enabled(pn.transition_name_to_id(t)))
    print("")

trace = ["record issue", "inspection", "intervention authorization", "work mandate", "work completion", "issue completion"]
for a in trace:
    check_enabled(mined_model)
    mined_model.fire_transition(mined_model.transition_name_to_id(a))




