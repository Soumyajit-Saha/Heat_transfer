# -*- coding: utf-8 -*-
"""
Created on Sat Mar  4 12:53:30 2023

@author: Soumyajit Saha
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# ASSUMPTIONS USED:
#   * THE COMPONENTS ARE FILLED WITH WATER INITIALLY AT ROOM TEMPERATURE  
#   * WHEN AN OUTFLOW OF WATER OCCURS FROM A COMPONENT IT IS IMMEDIATELY FILLED WITH NEW SOURCE OF WATER OF SAME VOLUME
#   * THE HEAT IS ENTIRELY TRANSFERED FROM COIL TO WATER IN HEATER
#   * HEAT LOSSES FROM PIPES AND PUMP ARE NEGLIGIBLE
#   * HEAT LOSSES FROM SOLAR PANEL AND STORANGE TANK TO ENVIRONMENT IS NEGLIGIBLE

secs_in_a_day = 86400

class Water:
    
    def __init__(self):
        self.specific_heat_of_water = 4182 #J/(Kg°C)
        
    def get_specific_heat(self):
        return self.specific_heat_of_water
    
class Component:
    
    def update(self):
        pass

class Solar_panel:
    
    def __init__(self):
        
        self.solar_panel_area = 1 #m^2
        self.voltage_of_solar_panel = 20 #V
        self.solar_power_in_a_day = np.array([0] * secs_in_a_day)
        
        self.solar_power_in_a_day[: int(1/8*secs_in_a_day)] = 0 #W/m^2
        self.solar_power_in_a_day[int(1/8*secs_in_a_day): int(2/8*secs_in_a_day)] = 100 #W/m^2
        self.solar_power_in_a_day[int(2/8*secs_in_a_day): int(3/8*secs_in_a_day)] = 500 #W/m^2
        self.solar_power_in_a_day[int(3/8*secs_in_a_day): int(4/8*secs_in_a_day)] = 700 #W/m^2
        self.solar_power_in_a_day[int(4/8*secs_in_a_day): int(5/8*secs_in_a_day)] = 1000 #W/m^2
        self.solar_power_in_a_day[int(5/8*secs_in_a_day): int(6/8*secs_in_a_day)] = 300 #W/m^2
        self.solar_power_in_a_day[int(6/8*secs_in_a_day): int(7/8*secs_in_a_day)] = 100 #W/m^2
        self.solar_power_in_a_day[int(7/8*secs_in_a_day): ] = 0 #W/m^2
        
        self.solar_current_in_a_day = self.solar_power_in_a_day * self.solar_panel_area / self.voltage_of_solar_panel #A
        
    def get_solar_current(self, i):
        return self.solar_current_in_a_day[i]
        
        

class Heater(Component):
    
    def __init__(self):
        
        self.solar_panel = Solar_panel()
        
        self.temp_of_coil = 22 #°C
        self.mass_of_coil = 1 #kg
        self.specific_heat_of_coil = 400 #J/(Kg°C)
        self.resistance_of_coil = 50 #ohm
        self.threshold_temperature_of_water_in_heater = 70 #°C
        self.capacity_of_heater = 100 #L
        self.temp_of_water_in_heater = 22 #°C
        self.water_from_heater_to_tank = 0
        
    def update_temperature(self, temp_of_water_in_tank):
        
        # WATER FLOWS FROM HEATER TO STORAGE TANK VIA PUMP AND SAME VOLUME OF WATER IS RETURNED TO HEATER FROM STORAGE TANK
        
        self.temp_of_water_in_heater = ((self.capacity_of_heater - self.water_from_heater_to_tank) * self.temp_of_water_in_heater + self.water_from_heater_to_tank * temp_of_water_in_tank ) / (self.capacity_of_heater)
     
    def heat_transfer(self, i, water):
        
        power_in_coil = self.solar_panel.get_solar_current(i)**2 * self.resistance_of_coil
        
        # ASSUMING ALL HEAT LOST BY THE COIL IS TRANSFERED TO WATER IN HEATER
        
        mass_of_water_in_heater = 1 * self.capacity_of_heater #kg
        
        change_in_temp_of_water_in_heater = power_in_coil * 1 / (water.specific_heat_of_water * mass_of_water_in_heater)
        
        self.temp_of_water_in_heater += change_in_temp_of_water_in_heater
        
        return power_in_coil
        
    def get_temperature(self):
        return self.temp_of_water_in_heater
    
    def get_threshold_temperature(self):
        return self.threshold_temperature_of_water_in_heater
    
    def update(self, pump, tank, sec, water):
        
        if self.get_temperature() >= self.get_threshold_temperature() and tank.get_temperature() < tank.get_threshold_temperature():
            if not pump.get_status():
                pump.turn_on()
                print('Pump started at ' + str(sec) + '.')
                
            self.water_from_heater_to_tank = pump.get_flow_rate() * 1 * 1000 #L
            
            self.update_temperature(tank.get_temperature())
            tank.update_temperature(self.water_from_heater_to_tank, self.get_temperature())
            
            if tank.temp_of_water_in_tank >= 50:
                print(tank.temp_of_water_in_tank)
        
        if self.get_temperature() < self.get_threshold_temperature():
            if pump.get_status():
                pump.turn_off()
                print('Pump stopped at ' + str(sec) + '.')
            power = self.heat_transfer(sec, water)
            print('Heat of ' + str(power) + ' W/m^2 transfered from coil to water in heater at ' + str(sec) + '.')
            
            
        if tank.get_temperature() >= tank.get_threshold_temperature() and pump.get_status():
            pump.turn_off()
            print('Pump stopped at ' + str(sec) + '.')
        
        
class Pump(Component):
    
    def __init__(self):
        self.flow_rate_of_pump = 0.00114 #m^3/s
        self.flag_flow = 0
       
    def turn_on(self):
        self.flag_flow = 1
        
    def turn_off(self):
        self.flag_flow = 0
        
    def get_status(self):
        return self.flag_flow
    
    def get_flow_rate(self):
        return self.flow_rate_of_pump
    
    def update(self):
        pass
       
class Storage_tank(Component):
    
    def __init__(self):
        self.capacity_of_storage_tank = 1000 #L
        self.start_time_of_outflow_from_tank = []
        self.duration_of_outflow_from_tank = []
        self.flow_rate = 0.0005 #m^3/s
        self.temp_of_water_in_tank = 22 #°C
        self.flag_flow = 0
        self.start = -1
        self.end = -1
        self.temp_of_outside = 22 #°C
        self.threshold_temperature_of_water_in_tank = 50 #°C
        self.water_flow = 0
      
    def get_temperature(self):
        return self.temp_of_water_in_tank
    
    def get_threshold_temperature(self):
        return self.threshold_temperature_of_water_in_tank
      
    def update_temperature(self, water_flow_to_heater, temp_of_water_in_heater):
        
        # WATER FLOWS FROM STORAGE TANK TO HEATER AND SAME VOLUME OF WATER IS RETURNED TO STORAGE TANK FROM HEATER VIA PUMP
        
        self.temp_of_water_in_tank = ((self.capacity_of_storage_tank - water_flow_to_heater) * temp_of_water_in_heater + water_flow_to_heater * self.temp_of_water_in_tank ) / (self.capacity_of_storage_tank)
      
    def get_start_times(self):
        return self.start_time_of_outflow_from_tank
    
    def set_start_times(self, hours, mins, secs):
        self.start_time_of_outflow_from_tank.append(int(hours)*3600 + int(mins)*60 + int(secs))
        
    def set_durations(self, duration):
        self.duration_of_outflow_from_tank.append(int(duration))
        
    def get_inflow(self):
        return self.flag_flow
    
    def set_inflow(self):
        self.flag_flow = 1
        
    def reset_inflow(self):
        self.flag_flow = 0
        
    def get_flow_rate(self):
        return self.flow_rate
    
    def set_start_end(self, start):
        self.start = start
        self.end = start + self.duration_of_outflow_from_tank[self.start_time_of_outflow_from_tank.index(start)]
        
    def reset_start_end(self):
        self.start = -1
        self.end = -1
        
    def get_end_time(self):
        return self.end
        
    def update_temperature_after_inflow_from_outside(self):
        
        # WATER FLOWS FROM STORAGE TANK TO DESTINATIONS AND SAME VOLUME OF WATER IS RETURNED TO STORAGE TANK FROM OUTSIDE SOURCE
        
        self.temp_of_water_in_tank = ((self.capacity_of_storage_tank - self.water_flow) * self.temp_of_water_in_tank + self.water_flow * self.temp_of_outside ) / (self.capacity_of_storage_tank)
    
    def update(self, sec):
        
        if sec in self.get_start_times():
            
            self.set_inflow()
            self.set_start_end(sec)
            
            
            print('Water outflow from Storage Tank started at ' + str(sec) + ' seconds.')
            
            # print(tank.start, tank.end)
            
            
        if self.get_inflow():
            
            self.water_flow = self.get_flow_rate() * 1 * 1000 #L
            self.update_temperature_after_inflow_from_outside()
            
            if sec == self.get_end_time():
                # print('end')
                print('Water outflow from Storage Tank stopped at ' + str(sec) + ' seconds.')
                self.reset_inflow()
                self.reset_start_end()
    
class Output:
    
    def __init__(self):
        self.temperatures_of_water_in_heater = []
        self.temperatures_of_water_in_tank = []
        
    def register_results(self, heater, tank):
        self.temperatures_of_water_in_heater.append(heater)
        self.temperatures_of_water_in_tank.append(tank)
        
    def get_heater_temperatures(self):
        return self.temperatures_of_water_in_heater
    
    def get_tank_temperatures(self):
        return self.temperatures_of_water_in_tank
    
    def animate(self, i):
        
        self.ax.clear()
        self.ax.plot([k for k in range(i)], self.get_heater_temperatures()[:i], linewidth=1, color='red', label='Heater')
        self.ax.plot([k for k in range(i)], self.get_tank_temperatures()[:i], linewidth=1, color='green', label='Storage Tank')
        self.ax.legend()
        self.ax.set_xlabel("Time(s)")
        self.ax.set_ylabel("Temperature in C°")
        self.ax.set_title("Temperature Changes in Heater and Storage Tank")
    
    def plot(self, is_animation):
        
        if is_animation == 'Y':
            
            self.fig, self.ax = plt.subplots()
            ani = FuncAnimation(self.fig, self.animate, frames=secs_in_a_day, interval=1, repeat=False)
    
            plt.show()
            
        else:
        
            plt.figure(figsize=(10,6))
            plt.plot([i for i in range(secs_in_a_day)], self.get_heater_temperatures(), linewidth=1, color='red', label='Heater')
            plt.plot([i for i in range(secs_in_a_day)], self.get_tank_temperatures(), linewidth=1, color='green', label='Storage Tank')
            plt.xlabel("Time(s)")
            plt.ylabel("Temperature in C°")
            plt.title("Temperature Changes in Heater and Storage Tank")
            plt.legend()
            plt.show()
            
    
class Simulation:
    
    def getInput(self, tank):
        self.is_animation = input("Do you want real time animation graph? (Y/N): ")
        no_of_inputs = input("Enter the number times you want water from storage tank: ")
        
        i = 0

        while i < int(no_of_inputs):
            time_of_day = input("Enter the time in format HH:MM:SS: ")
            duration = input("Enter duration in seconds: ")
            hours, mins, secs = time_of_day.split(':')
            
            if int(hours)*3600 + int(mins)*60 + int(secs) + int(duration) >= secs_in_a_day:
                continue
            
            tank.set_start_times(hours, mins, secs)
            tank.set_durations(duration)
            
            i += 1
    
    def run(self):
        water = Water()
        heater = Heater()
        
        pump = Pump()
        tank = Storage_tank()
        
        output = Output()
        
        self.getInput(tank)
        
        for sec in range(secs_in_a_day):
            
            # CHANGES IN HEATER
            
            heater.update(pump, tank, sec, water)
        
            
            # CHANGES IN TANK
            
            tank.update(sec)
             
                
            output.register_results(heater.get_temperature(), tank.get_temperature())
        
        # PLOTS
        
        output.plot(self.is_animation)
        
        
    

if __name__ == '__main__':
    Simulation().run()
        