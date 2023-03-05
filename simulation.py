# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 00:45:15 2023

@author: Soumyajit Saha
"""

class System:
    
    def handleEvents(self, events):
        pass
    
    def update(self):
        pass
    
    def registerReading(self):
        pass
  
class Heater(System):
    
    def handleEvents(self, events):
        print(self.__class__)
    
    def update(self):
        print(self.__class__)
    
    def registerReading(self):
        print(self.__class__)
    
class Pump(System):
    
    def handleEvents(self, events):
        print(self.__class__)
    
    def update(self):
        print(self.__class__)
    
    def registerReading(self):
        print(self.__class__)
    
class StorageTank(System):
    
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
        while True:
            for system in self.systems:
                system.handleEvents([])
        
            for system in self.systems:
                system.update()
    
            for system in self.systems:
                system.registerReading()
                
            break;
            
            
if __name__ == '__main__':
    Simulation().run()
