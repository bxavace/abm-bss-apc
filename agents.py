from mesa import Agent
from helper import calculate_travel_time

import math
import random

class Stop(Agent):
    """
    A stop in the bike sharing system. Each stop has queue line for shuttles and a number of bikes available.
    """
    def __init__(self, unique_id, model, pos, name):
        super().__init__(unique_id, model)
        self.pos = pos
        self.name = name
        self.shuttle_queue = []
        self.bikes_available = 10

class Shuttle(Agent):
    """
    A shuttle that moves between stops and transports passengers.
    """
    def __init__(self, unique_id, model, capacity, name):
        super().__init__(unique_id, model)
        self.capacity = capacity
        self.passengers = []
        self.current_stop = self.model.stops[0]
        self.next_stop_index = 1
        self.travel_time = 0
        self.idle_time = 0
        self.name = name

    def move(self):
        if self.travel_time > 0:
            self.travel_time -= 1
        else:
            if len(self.passengers) < self.capacity and self.current_stop.shuttle_queue:
                self.idle_time += 1
            else:
                self.idle_time = 0
                next_stop = self.model.stops[self.next_stop_index]
                self.travel_time = calculate_travel_time(self.current_stop.name, next_stop.name, 'shuttle')
                self.current_stop = next_stop
                self.next_stop_index = (self.next_stop_index + 1) % 3

    def load_passengers(self):
        while len(self.passengers) < self.capacity and self.current_stop.shuttle_queue:
            passenger = self.current_stop.shuttle_queue.pop(0)
            self.passengers.append(passenger)
            passenger.waiting_time = 0

    def unload_passengers(self):
        for passenger in self.passengers[:]: 
            if passenger.destination == self.current_stop.name:
                self.passengers.remove(passenger)
                passenger.current_stop = self.current_stop

    def step(self):
        self.unload_passengers()
        self.load_passengers()
        self.move()

class Person(Agent):
    def __init__(self, unique_id, model, origin, destination, person_type, weather):
        super().__init__(unique_id, model)
        self.origin = origin
        self.destination = destination
        self.current_stop = self.model.stops[ord(origin) - ord('A')]
        self.mode = None
        self.travel_time = 0
        self.person_type = person_type
        self.waiting_time = 0
        self.arrived = False
        self.weather = weather
    
    def calculate_utility(self, mode):
        waiting_time = self.waiting_time
        bike_avail = 1 if self.current_stop.bikes_available > 0 else 0
        shuttle_avail = 1 if len(self.current_stop.shuttle_queue) < 10 else 0

        factors = {
            'student': {
                # 'walk': (-0.080, 2.567, -0.169),
                # TEST: increase negative coefficient for walk
                # 'walk': (-3, 2.567, -0.169),
                # 'bike': (-2.941, 2.557, 1.117, -0.317),
                # 'shuttle': (-1.445, 1.855, 0.555, -0.214)
                'walk': (0, 0, 0),
                'bike': (0.5, 1, 2.5, -0.5),
                'shuttle': (0.752, 0.611, 0.99, -0.25)
            },
            'faculty': {
                # 'walk': (-0.080, -0.741, -0.169),
                # TEST: increase negative coefficient for walk
                # 'walk': (-3, -0.741, -0.169),
                # 'bike': (-2.941, 0.947, 1.117, -0.317),
                # 'shuttle': (-1.445, -0.125, 0.555, -0.214)
                'walk': (0, 0, 0),
                'bike': (-0.05, 0.235, 1.005, -1.03),
                'shuttle': (0.35, 0.05, 0.926, 0.341)
            }
        }

        if mode == 'walk':
            base, coef, weather_factor = factors[self.person_type][mode]
            return base + coef - (0.059 * waiting_time) + (self.weather * weather_factor)
        elif mode == 'bike':
            if bike_avail == 0:
                return -100
            base, coef, bike_coef, weather_factor = factors[self.person_type][mode]
            return base + coef + (bike_coef * bike_avail) - (0.059 * waiting_time) + (self.weather * weather_factor)
        elif mode == 'shuttle':
            base, coef, shuttle_coef, weather_factor = factors[self.person_type][mode]
            return base + coef + (shuttle_coef * shuttle_avail) - (0.059 * waiting_time) + (self.weather * weather_factor)


    def choose_mode(self):
        utilities = {}
        for mode in ['walk', 'bike', 'shuttle']:
            if mode == 'bike' and self.current_stop.bikes_available <= 0:
                continue
            utilities[mode] = self.calculate_utility(mode)

        ######################## TESTING: What if there is no bike system? ########################
        # utilities.pop('bike')
        ###########################################################################################

        total_exp_utility = sum(math.exp(u) for u in utilities.values())
        probabilities = {mode: math.exp(u) / total_exp_utility for mode, u in utilities.items()}
        
        rand = random.random()
        cumulative_prob = 0
        for mode, prob in probabilities.items():
            cumulative_prob += prob
            if rand <= cumulative_prob:
                self.mode = mode
                # print(f"Person {self.unique_id} chose {mode} with probability {prob}")
                break

        if self.mode == 'bike':
            self.current_stop.bikes_available -= 1

    def move(self):
        if self.travel_time > 0:
            self.travel_time -= 1
        elif self.current_stop.name == self.destination:
            self.arrived = True 
        elif self.mode == 'shuttle' and self not in self.current_stop.shuttle_queue:
            for agent in self.model.schedule.agents:
                if isinstance(agent, Shuttle) and agent.current_stop == self.current_stop and len(agent.passengers) < agent.capacity:
                    # print(f"Person {self.unique_id} got on Shuttle {agent.name}")
                    self.current_stop.shuttle_queue.append(self)
                    self.waiting_time += 1
                    break
            else:
                self.waiting_time += 1
        elif self.mode in ['bike', 'walk']:
            next_stop_index = (ord(self.current_stop.name) - ord('A') + 1) % 3
            next_stop = self.model.stops[next_stop_index]
            self.travel_time = calculate_travel_time(self.current_stop.name, next_stop.name, self.mode)
            self.current_stop = next_stop

    def step(self):
        if not self.mode:
            self.choose_mode()        
        if self.mode == 'shuttle' and self in self.current_stop.shuttle_queue:
            self.waiting_time += 1

        self.move()

        if self.arrived:
            if self.mode == 'bike':
                self.current_stop.bikes_available += 1
            self.model.remove_agent(self)