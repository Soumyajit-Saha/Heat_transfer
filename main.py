# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 00:45:15 2023

@author: Soumyajit Saha
"""
import numpy as np
from copy import deepcopy
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

eventQueue = []
secs_in_a_day = 84600

periodicTempInHeater = []
periodicTempInTank = []


class Event:
    pass


class PumpTriggerEvent(Event):
    def __init__(self, turnOn: bool):
        super().__init__()
        self.turnOn = turnOn


class PumpFlowRateEvent(Event):
    def __init__(self, flowRate: float):
        super().__init__()
        self.flowRate = flowRate


class TankTempThreshold(Event):
    def __init__(self, isCrossed: bool):
        super().__init__()
        self.isCrossed = isCrossed


class OutsideFlowEvent(Event):
    def __init__(self, turnOn: bool, flowRate: float):
        super().__init__()
        self.turnOn = turnOn
        self.flowRate = flowRate


class Water:
    def __init__(self, temp, vol):
        self.temperature = temp
        self.volume = vol
        self.specificHeat = 4182  # J/(Kg°C)


class WaterPacketEvent(Event):


    # volume, temperature
    def __init__(self, water: Water, flowType: str):
        super().__init__()
        self.water = water
        self.flowType = flowType


class System:
    def handleEvents(self, events):
        pass

    def update(self, delta: float):
        pass

    def registerReading(self):
        pass


class SolarPanel:
    def __init__(self):
        self.solarPanelArea = 1  # m^2
        self.voltageOfSolarPanel = 20  # V
        self.solarPowerInADay = np.array([0] * secs_in_a_day)

        self.solarPowerInADay[: int(1 / 8 * secs_in_a_day)] = 0  # W/m^2
        self.solarPowerInADay[int(1 / 8 * secs_in_a_day): int(2 / 8 * secs_in_a_day)] = 100  # W/m^2
        self.solarPowerInADay[int(2 / 8 * secs_in_a_day): int(3 / 8 * secs_in_a_day)] = 500  # W/m^2
        self.solarPowerInADay[int(3 / 8 * secs_in_a_day): int(4 / 8 * secs_in_a_day)] = 700  # W/m^2
        self.solarPowerInADay[int(4 / 8 * secs_in_a_day): int(5 / 8 * secs_in_a_day)] = 1000  # W/m^2
        self.solarPowerInADay[int(5 / 8 * secs_in_a_day): int(6 / 8 * secs_in_a_day)] = 300  # W/m^2
        self.solarPowerInADay[int(6 / 8 * secs_in_a_day): int(7 / 8 * secs_in_a_day)] = 100  # W/m^2
        self.solarPowerInADay[int(7 / 8 * secs_in_a_day):] = 0  # W/m^2

        self.solarCurrentInADay = self.solarPowerInADay * self.solarPanelArea / self.voltageOfSolarPanel  # A

    def getSolarCurrent(self, i):
        return self.solarCurrentInADay[i]


class Heater(System):
    def __init__(self):
        self.solarPanel = SolarPanel()

        self.waterPackets = [Water(temp=22, vol=100)]
        self.capacity = 100  # L
        self.thresholdTemp = 70  # °C
        self.resistanceOfCoil = 50  # ohm
        self.tankThresholdTempCrossed = False
        self.pumpStatus = False
        self.pumpFlowRate = 0

    def heatTransfer(self, i):
        powerInCoil = self.solarPanel.getSolarCurrent(i) ** 2 * self.resistanceOfCoil
        # ASSUMING ALL HEAT LOST BY THE COIL IS TRANSFERRED TO WATER IN HEATER
        massOfWaterInHeater = 1 * self.capacity  # kg
        water = self.getWater()
        changeInTempOfWaterInHeater = powerInCoil * 1 / (water.specificHeat * massOfWaterInHeater)
        water.temperature = water.temperature + changeInTempOfWaterInHeater
        self.setWater(water)
        return powerInCoil

    def getWater(self):
        return self.waterPackets[0]

    def setWater(self, water):
        self.waterPackets[0] = water

    def getHeaterTemperature(self):
        return self.waterPackets[0].temperature

    def handleEvents(self, events):
        for event in events:
            if type(event) is PumpTriggerEvent:
                self.pumpStatus = event.turnOn
                self.pumpFlowRate = 0 if not event.turnOn else self.pumpFlowRate

            if type(event) is PumpFlowRateEvent:
                self.pumpFlowRate = event.flowRate

            if type(event) is TankTempThreshold:
                self.tankThresholdTempCrossed = event.isCrossed

            if type(event) is WaterPacketEvent and event.flowType == 'tank_to_heater':
                self.waterPackets.append(event.water)

    def updateTemperature(self):
        nr, dr = 0, 0
        for water in self.waterPackets:
            nr += (water.temperature*water.volume)
            dr += water.volume

        self.waterPackets = [Water(temp=nr/dr, vol=dr)]

    def update(self, delta):
        if not self.pumpStatus and self.getHeaterTemperature() >= self.thresholdTemp and not self.tankThresholdTempCrossed:
            eventQueue.append(PumpTriggerEvent(turnOn=True))

        if self.pumpStatus:
            eventQueue.append(WaterPacketEvent(water=Water(temp=self.getHeaterTemperature(), vol=0.00114 * 1 * 1000), flowType='heater_to_tank'))
            self.waterPackets[0].volume -= (0.00114 * 1 * 1000)
            print(self.waterPackets[0].volume)
            print(self.waterPackets[0].temperature)

        self.updateTemperature()
        # print(self.waterPackets[0].temperature)

        if (self.getHeaterTemperature() < self.thresholdTemp) or (self.tankThresholdTempCrossed and self.pumpStatus):
            eventQueue.append(PumpTriggerEvent(turnOn=False))
            # always call self.updateTemperature() before self.heatTransfer()
            if self.getHeaterTemperature() < self.thresholdTemp:
                self.heatTransfer(delta)

    def registerReading(self):
        periodicTempInHeater.append(self.getHeaterTemperature())



class StorageTank(System):
    def __init__(self):
        self.waterPackets = [Water(temp=22, vol=1000)]
        self.capacity = 1000  # L
        self.thresholdTemperature = 50  # degree C
        self.outsideFlowRate = 0
        self.pumpFlowRate = 0
        # self.waterOutFlow

    def updateTemperature(self):
        nr, dr = 0, 0
        for water in self.waterPackets:
            nr += (water.temperature * water.volume)
            dr += water.volume

        self.waterPackets = [Water(temp=nr / dr, vol=dr)]
        # print(self.waterPackets[0].temperature)

    def setWater(self, water):
        self.waterPackets[0] = water

    def getTankTemperature(self):
        return self.waterPackets[0].temperature

    def handleEvents(self, events):
        for event in events:
            if type(event) is WaterPacketEvent and event.flowType == 'heater_to_tank':
                self.waterPackets.append(event.water)

            if type(event) is OutsideFlowEvent:
                self.outsideFlowRate = 0.0005 if event.turnOn else 0

    def update(self, delta: float):
        if self.outsideFlowRate:
            self.waterPackets.append(Water(temp=22, vol=(self.outsideFlowRate * 1 * 1000)))
            self.waterPackets[0].volume -= (self.outsideFlowRate * 1 * 1000)

        self.updateTemperature()

        if self.thresholdTemperature < self.getTankTemperature():
            eventQueue.append(TankTempThreshold(isCrossed=True))

    def registerReading(self):
        periodicTempInTank.append(self.getTankTemperature())


class OutletSystem(System):
    def __init__(self):
        self.start_time_of_outflow_from_tank = []
        self.duration_of_outflow_from_tank = []
        self.index = 0
        self.flowStatus = False

    def handleEvents(self, events):
        pass

    def update(self, time: float):
        if time in self.start_time_of_outflow_from_tank:
            eventQueue.append(OutsideFlowEvent(turnOn=True, flowRate=0.0005))
            self.index = self.start_time_of_outflow_from_tank.index(time)
            self.flowStatus = True

        if self.flowStatus and self.duration_of_outflow_from_tank[self.index]+self.start_time_of_outflow_from_tank[self.index] == time:
            eventQueue.append(OutsideFlowEvent(turnOn=False, flowRate=0))
            self.flowStatus = False

    def registerReading(self):
        pass

    def setTime(self, hours, mins, secs, duration):
        self.start_time_of_outflow_from_tank.append(int(hours) * 3600 + int(mins) * 60 + int(secs))
        self.duration_of_outflow_from_tank.append(int(duration))


is_animation = ''
fig, ax = None, None

def getInput(outletSystem: OutletSystem):
    global is_animation
    is_animation = input("Do you want real time animation graph? (Y/N): ")
    no_of_inputs = input("Enter the number times you want water from storage tank: ")

    i = 0
    while i < int(no_of_inputs):
        time_of_day = input("Enter the time in format HH:MM:SS: ")
        duration = input("Enter duration in seconds: ")
        hours, minutes, secs = time_of_day.split(':')

        if int(hours) * 3600 + int(minutes) * 60 + int(secs) + int(duration) >= secs_in_a_day:
            continue

        outletSystem.setTime(hours, minutes, secs, duration)
        i += 1

def animate(i):
    global fig, ax
    ax.clear()
    ax.plot([k for k in range(i)], periodicTempInHeater[:i], linewidth=1, color='red',
                  label='Heater')
    ax.plot([k for k in range(i)], periodicTempInTank[:i], linewidth=1, color='green',
                  label='Storage Tank')
    ax.legend()
    ax.set_xlabel("Time(s)")
    ax.set_ylabel("Temperature in C°")
    ax.set_title("Temperature Changes in Heater and Storage Tank")

def plot():
    global is_animation, fig, ax
    if is_animation == 'Y':
        fig, ax = plt.subplots()
        ani = FuncAnimation(fig, animate, frames=secs_in_a_day, interval=1, repeat=False)
    
        plt.show()
    else:
        plt.figure(figsize=(10, 6))
        plt.plot([i for i in range(secs_in_a_day)], periodicTempInHeater, linewidth=1, color='red', label='Heater')
        plt.plot([i for i in range(secs_in_a_day)], periodicTempInTank, linewidth=1, color='green', label='Storage Tank')
        plt.xlabel("Time(s)")
        plt.ylabel("Temperature in C°")
        plt.title("Temperature Changes in Heater and Storage Tank")
        plt.legend()
        plt.show()


class Simulation:
    def __init__(self):
        self.systems = [Heater(), StorageTank(), OutletSystem()]
        self.outletEvents = []
        getInput(self.systems[-1])

    def run(self):
        global eventQueue
        for i in range(secs_in_a_day):
            oldEvents = deepcopy(eventQueue)
            eventQueue = []
            for system in self.systems:
                system.handleEvents(oldEvents)

            for system in self.systems:
                system.update(i)

            for system in self.systems:
                system.registerReading()

        plot()


if __name__ == '__main__':
    Simulation().run()
