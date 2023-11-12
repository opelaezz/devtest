import random
import pandas as pd
import numpy as np
# first, simulate a set of demands (or not demandas, that is when destination floor = current floor)
ncalls = 500 # demands made during a week
start_date = '2023-11-01'
end_date = '2023-11-07'
# Generate random datetime calls (seconds frequency)
num_seconds = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).total_seconds()
random_seconds = np.random.randint(0, int(num_seconds), size=500)
random_datetimes = pd.to_datetime(start_date) + pd.to_timedelta(random_seconds, unit='s')

# A dataframe recording elevator calls
# iniTime: hour at whic a person calls the elevator
# destinations: floor
destinations = random.choices(range(10), k=ncalls)
demands = pd.DataFrame({'iniTime': random_datetimes, 'destinations': destinations})
demands = demands.sort_values(['iniTime'])
demands = demands.reset_index(drop=True)

##### Define the Elevator class #####
# call_time: time whnen the person calls the elevator
# lastfloor: elevator's last position
# last_time: datetime registered at the last position
class Elevator:
    def __init__(self, lastfloor, call_time, last_time):
        self.current_floor = lastfloor
        self.direction = "rest"
        self.passengers = []
        self.last_time = last_time
        self.call_time = call_time        
        self.eleva_busy = None
    
    def move(self, init_floor, target_floor):
        # elevator movement logic
        if self.current_floor == init_floor:
            self.direction = "rest"
            self.current_floor += 0
        elif self.current_floor > target_floor:
            self.direction = "above"
            self.current_floor -= 1
        else:
            self.direction = "below"
            self.current_floor += 1
        

    def state(self, target_time):
            if (self.last_time >= target_time) & (self.direction != "rest"):
                self.eleva_busy = 1
            elif self.direction == "rest":
                self.eleva_busy = 0            
            else:
                self.eleva_busy = 0           
      

    def load_passenger(self, passenger):        
        if passenger in self.passengers:
            self.passengers.append(passenger)

    def unload_passenger(self, passenger):
        # unloading a passenger
        if passenger in self.passengers:
            self.passengers.remove(passenger)

        
##### Define the Demand class #####
# floors: bulding floors
# call_time: datetime, whnen the person calls the elevator
# lastfloor: elevator's last position
# last_time: time recorded at the last position
class Demand:
    def __init__(self, floors, elevator, call_time, lastfloor, last_time):
        self.current_floor = random.choice(floors)
        #self.destination_floor = random.choice([f for f in floors if f != self.current_floor])
        self.destination_floor = None
        self.lastfloor = lastfloor
        # spent time goin from last floor to the floor where the demand is made
        self.time_reach = pd.to_timedelta(abs(self.lastfloor - self.current_floor) * 5, unit='s')
        # spent time going from the floor where the demand is made to the destination
        self.travel_time = None

        self.call_time = call_time
        self.last_time = last_time
        self.enter_time = None
        self.leave_time = None
        self.wait_time = None
        self.eleva_busy = None        
        self.elevator = elevator     

    def request_elevator(self):
        # Record the time when the passenger calls the elevator
        
        self.elevator.load_passenger(self)
        passenger_floor = self.current_floor
        destination_floor = self.destination_floor        
        cal_time = self.call_time
        self.elevator.state(cal_time)
        self.wait()
        self.elevator.move(passenger_floor, destination_floor)
        #self.elevator.move(destination_floor)
        self.elevator.unload_passenger(self)        
        self.exit_elevator()

    def wait(self):
                
        # waiting time
        if self.lastfloor == self.current_floor:
            # if the elevator is at the same floor that the person
            self.wait_time = pd.to_timedelta(3, unit='s') # while the doors open
        
        elif (self.eleva_busy == 1) & (self.last_time >= self.call_time):
            # for a busy elevator
            self.wait_time = (self.last_time - self.call_time) + self.time_reach
        else:
            self.wait_time = self.time_reach
        
        self.enter_time = self.call_time + self.wait_time
 
    def exit_elevator(self):
        self.travel_time = pd.to_timedelta(abs(self.destination_floor - self.current_floor) * 5, unit='s')        
        # Record the time when the passenger exits the elevator        
        self.leave_time = self.enter_time + self.time_reach + self.travel_time
        
######## Process for collecting elevator information #######
# Database connection
import psycopg2
'''conn = psycopg2.connect(host="localhost",database="MyDataBase",user="username",password="password")
cur = conn.cursor()
# insert into elevator table
insert_sql = """
    INSERT INTO elevator (call_time, enter_time, leave_time,wait_time,travel_time, current_floor, destination_floor, elevator_last_position)
    VALUES (%(call_time)s, %(enter_time)s, %(leave_time)s, %(wait_time)s, %(travel_time)s, %(current_floor)s, %(destination_floor)s, %(elevator_last_position)s,)
"""   ''' 
# Simulation parameters (first demand)
num_floors = 10
lastfloor = random.choice(range(num_floors))
enter_time = demands['iniTime'][0] + pd.to_timedelta(40, unit='s') 
last_time = enter_time + pd.to_timedelta(90, unit='s')
eleva_busy = 0

##### Generating results for 500 demandas
elevator_dyn = pd.DataFrame()
for i in demands.index:

    call_time = demands['iniTime'][i]
    destination_floor = demands['destinations'][i]

    # Create an elevator
    #elevator = Elevator(range(num_floors), last_time, call_time)
    elevator = Elevator(lastfloor, last_time, call_time)


    # Create a passenger with the desired destination    
    passenger = Demand(range(num_floors), elevator, call_time, lastfloor, last_time)
    # The passenger choose floor i
    passenger.destination_floor = destination_floor
    passenger.eleva_busy =  eleva_busy 
    # Request an elevator for the passenger
    passenger.request_elevator()

    # Passenger enters the elevator
    passenger.wait()

    # Passenger exits the elevator
    passenger.exit_elevator()  

    # Record results
    results_demand = {'call_time': passenger.call_time, 'enter_time': passenger.enter_time, 'leave_time': passenger.leave_time,
                       'wait_time': passenger.wait_time, 'travel_time':passenger.travel_time,
                       'current_floor': passenger.current_floor, 'destination_floor':passenger.destination_floor,
                         'elevator_last_position': elevator.direction}
    # inserting the results from demand i
    #cur.execute(insert_sql, results_demand)
    
    elevator_dyn = pd.concat([elevator_dyn, pd.DataFrame(results_demand, index = [0])])

    # update data for the next demand
    last_time = passenger.leave_time
    lastfloor = passenger.destination_floor # where the elevator is resting now
    eleva_busy = elevator.eleva_busy        # the elevator occupied or not
