class PetriNet():
    def __init__(self):
        self.places = []
        self.transitions = {}
        self.edges = {}
        self.tokens = {}
        self.markings = {}
        self.is_enabled_dict = {}
        self.fired_transition = {}

    def add_place(self, name):
        self.places.append(name)
        self.tokens[name] = 0
        self.markings[name] = 0
        return self

    def add_transition(self, name, id):
        if id not in self.transitions:
            self.transitions[id] = []
        self.transitions[id].append(name)
        return self

    def add_edge(self, source, target):
        if source not in self.edges:
            self.edges[source] = []
        self.edges[source].append(target)
        return self

    def get_tokens(self, place):
        return self.tokens.get(place, 0)

    def is_enabled(self, transition):
        incoming_places = [place for place in self.edges if transition in self.edges[place]]
        for place in incoming_places:
            if self.tokens[place] <= 0:
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
        return self