

# class PetriNet():
#     places = []
    
#     transitions = dict.fromkeys([],[])
    
#     edges = dict.fromkeys([],[])
    
#     tokens = dict.fromkeys([],[])
    
#     markings = dict.fromkeys([],[])
    
#     is_enabled = dict.fromkeys([],[])
    
#     fired_transition = dict.fromkeys([],[])
    

#     def __init__(self):
#         # code here

#     def add_place(self, name):
#         self.places.append(name)

#     def add_transition(self, name, id):
#         self.transitions[id].append(name)

#     def add_edge(self, source, target):
#         self.edges[source].append(target)

#     def get_tokens(self, place):
        

#     def is_enabled(self, transition):
        

#     def add_marking(self, place):
        

#     def fire_transition(self, transition):
#         # code here

# # etc

class PetriNet():
    def __init__(self):
        self.places = []  # List of places
        self.transitions = {}  # Dictionary for transitions with dynamic keys
        self.edges = {}  # Dictionary for edges with dynamic keys
        self.tokens = {}  # Dictionary for tokens count in each place with dynamic keys
        self.markings = {}  # Dictionary for markings in each place with dynamic keys
        self.is_enabled_dict = {}  # Dictionary for transition enable status with dynamic keys
        self.fired_transition = {}  # Dictionary for fired transitions with dynamic keys

    def add_place(self, name):
        self.places.append(name)
        self.tokens[name] = 0  # Initialize token count for this place
        self.markings[name] = 0  # Initialize markings for this place

    def add_transition(self, name, id):
        if id not in self.transitions:
            self.transitions[id] = []  # Initialize transition with a list if not already present
        self.transitions[id].append(name)

    def add_edge(self, source, target):
        if source not in self.edges:
            self.edges[source] = []  # Initialize edges with a list if not already present
        self.edges[source].append(target)

    def get_tokens(self, place):
        return self.tokens.get(place, 0)  # Return the number of tokens in a place

    def is_enabled(self, transition):
        # Check if the transition is enabled
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

# Test cases
p = PetriNet()

p.add_place(1)
p.add_place(2)
p.add_place(3)
p.add_place(4)
p.add_transition("A", -1)
p.add_transition("B", -2)
p.add_transition("C", -3)
p.add_transition("D", -4)

p.add_edge(1, -1)
p.add_edge(-1, 2)
p.add_edge(2, -2)
p.add_edge(-2, 3)
p.add_edge(2, -3)
p.add_edge(-3, 3)
p.add_edge(3, -4)
p.add_edge(-4, 4)

print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.add_marking(1)
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-1)
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-3)
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-4)
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.add_marking(2)
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-2)
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

p.fire_transition(-4)
print(p.is_enabled(-1), p.is_enabled(-2), p.is_enabled(-3), p.is_enabled(-4))

print(p.get_tokens(4))
