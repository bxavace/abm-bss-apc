from mesa import Model
from mesa.time import RandomActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector
from agents import Person, Stop, Shuttle
from scipy.stats import poisson

import random
import numpy as np


class TransportationModel(Model):
    def __init__(self):
        self.schedule = RandomActivation(self)
        self.space = ContinuousSpace(1100, 100, True)
        self.stops = [Stop(i, self, (x, y), name) for i, (x, y, name) in enumerate([(0, 50, "A"), (450, 50, "B"), (1100, 50, "C")])]

        for stop in self.stops:
            self.schedule.add(stop)
            self.space.place_agent(stop, stop.pos)
        
        self.shuttleA = Shuttle(len(self.stops), self, 21, "A")
        self.schedule.add(self.shuttleA)
        self.num_agents = 0
        
        self.datacollector = DataCollector(
            model_reporters={
                "Average Waiting Time": lambda m: np.mean(
                    [agent.waiting_time for agent in m.schedule.agents 
                    if isinstance(agent, Person) and any(agent in stop.shuttle_queue for stop in m.stops)]
                ) if any(isinstance(agent, Person) for agent in m.schedule.agents) else 0,
                "Queue Length A": lambda m: len(m.stops[0].shuttle_queue),
                "Queue Length B": lambda m: len(m.stops[1].shuttle_queue),
                "Queue Length C": lambda m: len(m.stops[2].shuttle_queue),
                "Bikes at A": lambda m: m.stops[0].bikes_available,
                "Bikes at B": lambda m: m.stops[1].bikes_available,
                "Bikes at C": lambda m: m.stops[2].bikes_available,
                "Arrival Rate": lambda m: m.rate_function(m.current_time),
                "People Choosing Shuttle": lambda m: m.count_people_by_mode()['shuttle'],
                "People Choosing Bike": lambda m: m.count_people_by_mode()['bike'],
                "People Choosing Walk": lambda m: m.count_people_by_mode()['walk']
            }
        )
        self.start_time = 6 * 60  # 6:00 AM in minutes since midnight
        self.end_time = 19 * 60   # 7:00 PM in minutes since midnight
        self.current_time = self.start_time
        self.weather = random.randint(0, 1)

    def count_people_by_mode(self):
        """
        Count the number of people using each mode of transportation.
        """
        modes = {'shuttle': 0, 'bike': 0, 'walk': 0}
        for agent in self.schedule.agents:
            if isinstance(agent, Person):
                if agent.mode in modes:
                    modes[agent.mode] += 1
        return modes

    def add_person(self, origin, destination, person_type):
        person = Person(self.num_agents + len(self.stops) + 1, self, origin, destination, person_type, self.weather)
        # DEBUG purpose
        # print(f"Weather is {['good', 'bad'][self.weather]}")
        self.schedule.add(person)
        self.num_agents += 1

    def remove_agent(self, agent):
        self.schedule.remove(agent)
        if isinstance(agent, Person):
            self.num_agents -= 1

    def rate_function(self, t):
        """
        Define the time-varying arrival rate function.
        t: time in minutes since start of the day (6:00 AM)
        """
        t = t - self.start_time  # Adjust t to be minutes since 6:00 AM
        morning_peak = 0.50 * np.exp(-((t - 120) / 60) ** 2)  # Peak at 8:00 AM, before: 0.9
        lunch_peak = 0.15 * np.exp(-((t - 390) / 60) ** 2)  # Peak at 12:30 PM, before: 0.35
        evening_peak = 0.35 * np.exp(-((t - 660) / 45) ** 2)  # Stronger peak at 5:00 PM, before: 0.7
        base_rate = 1  # Base arrival rate
        
        return max(base_rate + morning_peak + lunch_peak + evening_peak, 0)
    
    def destination_probabilities(self, t):
        """
        Define the time-varying destination probabilities.
        """
        if t < 480:  # Before 8 AM
            return {
                ('A', 'C'): 0.9, ('C', 'A'): 0.005, ('B', 'C'): 0.0,
                ('C', 'B'): 0.0, ('A', 'B'): 0.01, ('B', 'A'): 0.085
            }
        elif 690 <= t < 810:  # Between 11:30 AM and 1:30 PM
            return {
                ('A', 'C'): 0.1, ('C', 'A'): 0.8, ('B', 'C'): 0.0,
                ('C', 'B'): 0.0, ('A', 'B'): 0.05, ('B', 'A'): 0.05
            }
        elif t >= 1020:  # After 5 PM
            return {
                ('A', 'C'): 0.08, ('C', 'A'): 0.85, ('B', 'C'): 0.0,
                ('C', 'B'): 0.0, ('A', 'B'): 0.035, ('B', 'A'): 0.035
            }
        else:  # Default probabilities
            return {
                ('A', 'C'): 0.45, ('C', 'A'): 0.45, ('B', 'C'): 0.0,
                ('C', 'B'): 0.0, ('A', 'B'): 0.05, ('B', 'A'): 0.05
            }
        # DEBUG: Disable the probabilities of Stop B
        # if t < 480:  # Before 8 AM
        #     return {
        #         ('A', 'C'): 0.995, ('C', 'A'): 0.005
        #     }
        # elif 690 <= t < 810:  # Between 11:30 AM and 1:30 PM
        #     return {
        #         ('A', 'C'): 0.6, ('C', 'A'): 0.4
        #     }
        # elif t >= 1020:  # After 5 PM (end of school day)
        #     return {
        #         ('A', 'C'): 0.005, ('C', 'A'): 0.995
        #     }
        # else:  # Default probabilities
        #     return {
        #         ('A', 'C'): 0.5, ('C', 'A'): 0.5
        #     }

    def get_arrival_rates(self):
        """
        Get the arrival rates for each minute of the day.
        """
        times = range(self.start_time, self.end_time, 1)
        rates = [self.rate_function(t) for t in times]
        # Debug print, print the arrival rates for each minute
        # for t, r in zip(times, rates):
        #     print(f"Time: {t // 60:02d}:{t % 60:02d}, Arrival Rate: {r:.2f}")
        return times, rates
    
    def step(self):
        """
        Advance the model by one step.
        """
        if self.current_time >= self.end_time:
            return  # End the simulation if we've reached 6 PM

        # Calculate the expected number of arrivals for this time step
        rate = self.rate_function(self.current_time)
        num_arrivals = poisson.rvs(rate * 1)
        
        destination_probabilities = self.destination_probabilities(self.current_time)
        
        for _ in range(num_arrivals):
            origin, destination = random.choices(list(destination_probabilities.keys()), 
                                                 weights=list(destination_probabilities.values()))[0]
            person_type = 'student' if random.random() < 0.8 else 'faculty'
            # print(f"Person {self.num_agents + 1} arrived at {origin} and going to {destination}")
            self.add_person(origin, destination, person_type)

        self.schedule.step()
        self.datacollector.collect(self)
        self.current_time += 1