# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 00:45:15 2023

@author: Soumyajit Saha
"""
import numpy as np


eventQueue = ['water_temp_in_tank_below_threshold:22:50']
secs_in_a_day = 84600

periodicTempInHeater = []
periodicTempInTank = []

class Event:
    
    def __init__(self, msg):
        self.msg = msg
        self.handled = False
        
    def isHandled(self):
        return self.handled
    
    def setHandle(self):
        self.handled = True
        
    def getMsg(self):
        return self.msg
    

class Water:
    def __init__(self, temp, vol):
        self.temperature = temp
        self.volume = vol
        self.specificHeat = 4182 #J/(Kg°C)
        
    def getTemp(self):
        return self.temperature
    
    def setTemp(self, temp):
        self.temperature = temp

class System:
    
    def handleEvents(self, events):
        pass
    
    def update(self):
        pass
    
    def registerReading(self):
        pass

class SolarPanel:
    
    def __init__(self):
        
        self.solarPanelArea = 1 #m^2
        self.voltageOfSolarPanel = 20 #V
        self.solarPowerInADay = np.array([0] * secs_in_a_day)
        
        self.solarPowerInADay[: int(1/8*secs_in_a_day)] = 0 #W/m^2
        self.solarPowerInADay[int(1/8*secs_in_a_day): int(2/8*secs_in_a_day)] = 100 #W/m^2
        self.solarPowerInADay[int(2/8*secs_in_a_day): int(3/8*secs_in_a_day)] = 500 #W/m^2
        self.solarPowerInADay[int(3/8*secs_in_a_day): int(4/8*secs_in_a_day)] = 700 #W/m^2
        self.solarPowerInADay[int(4/8*secs_in_a_day): int(5/8*secs_in_a_day)] = 1000 #W/m^2
        self.solarPowerInADay[int(5/8*secs_in_a_day): int(6/8*secs_in_a_day)] = 300 #W/m^2
        self.solarPowerInADay[int(6/8*secs_in_a_day): int(7/8*secs_in_a_day)] = 100 #W/m^2
        self.solarPowerInADay[int(7/8*secs_in_a_day): ] = 0 #W/m^2
        
        self.solarCurrentInADay = self.solar_power_in_a_day * self.solar_panel_area / self.voltage_of_solar_panel #A
        
    def getSolarCurrent(self, i):
        return self.solarCurrentInADay[i]    

class Heater(System):
    
    def __init__(self):
        
        self.solarPanel = SolarPanel()
        
        self.water = Water(22, 100)
        self.capacity = 100 #L
        self.thresholdTemp = 70 #°C
        self.inFlowWater = None
        self.outFlowWater = None
        self.tempOfCcoil = 22 #°C
        self.massOfCoil = 1 #kg
        self.specificHeatOfCoil = 400 #J/(Kg°C)
        self.resistanceOfCoil = 50 #ohm
        self.tankTemp = 0
        self.tankThresholdTemp = 0
        self.pumpStatus = False
        self.pumpFlowRate = 0
        
    def heatTransfer(self, i, water):
        
        powerInCoil = self.solarPanel.getSolarCurrent(i)**2 * self.resistanceOfCoil
        
        # ASSUMING ALL HEAT LOST BY THE COIL IS TRANSFERED TO WATER IN HEATER
        
        massOfWaterInHeater = 1 * self.capacityOfHeater #kg
        
        changeInTempOfWaterInHeater = powerInCoil * 1 / (self.water.specificHeat * massOfWaterInHeater)
        
        self.water.setTemp(self.water.getTemp + changeInTempOfWaterInHeater)
        
        return powerInCoil   
    
    def getWaterTemperature(self):
        return self.water.temperature
    
    def handleEvents(self, events):
        
        for event in eventQueue:
            
            if 'in_flow_from_tank_to_heater' in event.msg:
                self.inFlowWater = Water(int(event.msg.split(':')[1]), int(event.msg.split(':')[2]))
                event.setHandle()
                
            elif event.getMsg() == 'water_temp_in_tank_below_threshold':
                self.tankTemp = int(event.split(':')[1])
                self.tankThresholdTemp = int(event.split(':')[2])
                
            elif event.getMsg() == 'water_temp_in_tank_above_threshold':
                self.tankTemp = int(event.split(':')[1])
                self.tankThresholdTemp = int(event.split(':')[2])
                
            elif 'pump_on' in event.getMsg():
                self.pumpStatus = True
                self.pumpFlowRate = int(event.getMsg().split(':')[1])
                
            elif 'pump_off' in event.getMsg():
                self.pumpStatus = False
                self.pumpFlowRate = int(event.getMsg().split(':')[1])
                
    def updateTemperature(self):
        self.water.setTemp(((self.capacityOfHeater - self.inFlowWater) * self.water.getTemp() + self.inFlowWater * self.tankTemp ) / (self.capacityOfHeater))
                
    
    def update(self):
        
        if self.getWaterTemperature() >= self.thresholdTemp and self.tankTemp < self.tankThresholdTemp:
            if not self.pumpStatus():
                eventQueue.append(Event('pump_on:' + str(self.flowRate)))
                
            water = self.pumpFlowRate * 1 * 1000 #L
            
            self.updateTemperature()
            
            eventQueue.append('in_flow_from_heater_to_tank:' + str(water) + ':' + str(self.getWaterTemperature()))
        
        if self.getWaterTemperature() < self.thresholdTemp:
            eventQueue.append(Event('pump_off:' + str(self.flowRate)))
            self.heatTransfer()
            
        if self.tankTemp >= self.tankThresholdTemp and self.pumpStatus:
            eventQueue.append(Event('pump_off:' + str(self.flowRate)))
    
    def registerReading(self):
        periodicTempInHeater.append(self.getWaterTemperature())
    
class Pump(System):
    
    def __init__(self):
        self.flowRate = 0.00114 #m^3/s
        self.isOn = False
        
    def getFlowRate(self):
        return self.flowRate
    
    def turnOn(self):
        self.isOn = True
        
    def turnOff(self):
        self.isOn = False
    
    def handleEvents(self):
        
        for event in eventQueue:
        
            if 'pump_on' in event.getMsg():
                self.turnOn()
                
            elif 'pump_off' in event.getMsg():
                self.turnOff()
    
    def update(self):
        pass
    
    def registerReading(self):
        pass
    
class StorageTank(System):
    
    def __init__(self):
        self.water = Water(22, 1000)
        self.capacity = 1000 #L
    
    def handleEvents(self, events):
        print(self.__class__)
    
    def update(self):
        print(self.__class__)
    
    def registerReading(self):
        print(self.__class__)
        
class Simulation:
    def __init__(self):
        self.systems = [Heater(), Pump(), StorageTank()]

    def run(self):
        for i in range(secs_in_a_day):
            for system in self.systems:
                system.handleEvents([])
        
            for system in self.systems:
                system.update()
    
            for system in self.systems:
                system.registerReading()
                
            
            
if __name__ == '__main__':
    Simulation().run()
