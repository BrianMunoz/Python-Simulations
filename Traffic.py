""" WSUTraffic """
from SimPy.Simulation import *
from random import expovariate, seed, random, gauss

## @package Traffic
# This package satisfies the requirements of WSUTraffic
# As started in Requirements.docx


class Model:
   SimDuration = 3600.0
   SimulationStepTimeS = 1  # Recalculate vehicle positions at
                              # 1/SimulationStepTimeS Hz
   SpeedLimit = 0             # Km/h
   #REQ: 0013
   RoadLength = 34000.0          # meters
   specialCarTravelTime = 0
   def __init__(self):
      self.carsExitingHighway = 0
      self.crashedCars = 0

## VehicleGenerator
# This process generates new Vehicle instances at a periodic rate
# defined by period argument to this method.
# This process stes each generated vehicles initial position,
# initial speed, and preceding vehicle.
# Req: 0008, 0010, 0011, 0016, 0017, 0018
class VehicleGenerator(Process):
   """ """
   def __init__(self):
      Process.__init__(self)
      self.carNumber = 1
      self.lastCar = None
   ## generate
   # This Process Execution Method (PEM)
   #    adds Vehicle instances to the road at a specified periodic
   # rate.
   def generate(self, period, model):
      while 1:
         if (now() % period) < 0.1: #floating point error, so anything less then .1 is basically zero
            name = 'car %d' % self.carNumber
            startSpeed = model.SpeedLimit * 1.05
            startSpeed = expovariate(1.0/startSpeed)
          
            #if there is no last car, then create a car process with out a
            #preceding car, then assign this car to last car.
            if self.lastCar is None:
               car = Car(name, startSpeed, None)
               activate (car, car.travel(model))
               self.lastCar = car
               self.carNumber += 1
            else:
               car = Car(name, startSpeed, self.lastCar)
               #track the car entering at 49 minutes after the simulation statt
               #Req 0016, 0017, 0018
               if now() >= 49.0 and now() <= 50.0:
                  car.isSpecialCar = 1
               activate(car, car.travel(model))
               self.lastCar = car
               self.carNumber += 1
               
                  
         yield hold, self, model.SimulationStepTimeS

## Vehicle

class Car(Process):
   def __init__(self, name, currentSpeed, precedingCar):
      Process.__init__(self, name)
      self.currentSpeed = currentSpeed       # Km/h speed the car is currently travelling
      self.defaultSpeed = currentSpeed		 # Km/h speed the car entered the highway at
      self.currentPosition = 0.0    # meters
      self.entryTime = now()
      self.precedingCar = precedingCar
      self.state = 1
      self.isSpecialCar = 0
      
   def getPosition(self):
      return self.currentPosition

   ## separationInSeconds
   #  Returns calculated separation from preceding vehicle in units
   # of seconds (travelling at current speed)
   # Req: 0002
   def separationInSeconds(self):
      """ """
      if self.precedingCar is None:
         return 0.0
      # current speed in m/s meters per kilometer / seconds per hour
      currentSpeedMperS = self.currentSpeed * 1000.0 / 3600.0
      currentSeparationM = self.precedingCar.getPosition() - self.getPosition()
      if currentSeparationM <= 0:
         # we have detected a collision
         #Req: 0014, 0015         
         currentSeparationS = 0.0
      else:
        # distance equals speed times time
         currentSeparationS = currentSeparationM / currentSpeedMperS
      return currentSeparationS
   ## collisionFromBehind
   #  This function passivates the process if there is a
   #  collision and the process is a proceeding car
   def collisionFromBehind(self):
      self.state = 0
      yield passivate, self

   ## travel
   # This Process Execution Method (PEM)
   # - calculates vehicle position
   #   based on current simulation time, current speed, and time elapsed
   # since last calculation of separationInSeconds.
   # - Set current speed based on Req. 0003, 0004, 0005
   # - Detect crashes based on Req 0014, 0015
   def travel(self, model):
      """ """
      while 1:   
         
         if self.precedingCar is not None:
            if self.precedingCar.state == 1:
               currentSeparationS = self.separationInSeconds()
               if currentSeparationS <= 0.0:
                  # Crash
                  #print 'CRASH between {} and {}'.format( self.precedingCar.name, self.name)
                  #print self.currentPosition, self.precedingCar.currentPosition
                  model.crashedCars += 2
                  self.precedingCar.collisionFromBehind()
                  self.state = 0
                  self.precedingCar.state = 0
                  yield passivate, self
                  break
               elif currentSeparationS < 0.5:
                  # Panic mode; slowdown to 5% of the speed limit
                  
                  self.currentSpeed = model.SpeedLimit * .05
               elif currentSeparationS < 1.0:
                  # Caution mode; slow do to 15% under the speed limit
                  self.currentSpeed = self.currentSpeed * .85
               elif currentSeparationS > 2.0:
                  # Normal mode
                  self.currentSpeed = self.defaultSpeed
               else:
                  # between Caution and Normal
                  self.currentSpeed = model.SpeedLimit
         
         if self.currentPosition < model.RoadLength and self.state == 1:    
            currentSpeedMperS = self.currentSpeed * 1000.0 / 3600.0
            self.currentPosition += currentSpeedMperS * model.SimulationStepTimeS
         elif self.currentPosition >= model.RoadLength and self.state == 1:
            # increment count of vehicles leaving the road
            model.carsExitingHighway += 1
            travelTime = now() - self.entryTime
            if self.isSpecialCar == 1:
               model.specialCarTravelTime = travelTime
            self.state = 0
            yield passivate, self
            break

         yield hold, self, model.SimulationStepTimeS


## Scenario definition
# This class hold a pair of speedLimits and entry rates that define scenarios

class Scenario:
   def __init__(self, period):
      # Req 0008, 0010, 0011, 0016, 0017, 0018
      self.period = period
      self.speedLimits = [100, 120, 140]
##Definition of ExpirementValues
# This object allows all values to be remember while simulation runs
# When sim is over, predictions shall be made based on Req: 0008, 0010, 0011, 0016, 0017, 0018
class ExpirementValues:
   def __init__(self):
      self.specialCarTravelTimes = []
      self.carsFullyTravel = []
      self.scenarios = [Scenario(4),
                        Scenario(2),
                        Scenario(1) ]
      

## runSimulation definition
# Run the sim and print results for each iteration
# Req: 0001 thru 0018
def runSimulation(exp, period, speedLimit):
   seed(42)
   model = Model()
   model.SpeedLimit = speedLimit
   initialize()
   scen1Gen = VehicleGenerator()
   scen2Gen = VehicleGenerator()
   scen3Gen = VehicleGenerator()
   activate(scen1Gen, scen1Gen.generate(period, model) )

   simulate(until = model.SimDuration)

   exp.specialCarTravelTimes.append(model.specialCarTravelTime)
   exp.carsFullyTravel.append(model.carsExitingHighway)
   
   if speedLimit == 120:
      #Req: 0014
      print '{} crashes occured at {}kmph speed limit'.format(model.crashedCars, speedLimit)
   
   print '{} safely exited the highway'.format(model.carsExitingHighway)

   
def findSpeedLimit(toFind, limits):
   for i in range(0,len(limits)):
      if toFind == limits[i]:
         if i == 0:
            return 100
         if i == 1:
            return 120
         if i == 2:
            return 140

def findFastSpecialCarTime(times):
   temp = min(times)
   for i in range(0,len(times)):
      if temp > 0:
         if temp == times[i]:
            if i == 0:
               return [temp, 100]
            if i == 1:
               return [temp, 120]
            if i == 2:
               return [temp, 140]
   
## Experiment/Result printer
# Req 0014, 0009, 0010, 0011, 0016, 0017, 0018
exp = ExpirementValues()
print '\n'
for i in range(0, len(exp.scenarios)):
   print 'Scenario {}: '.format(i + 1)
   print '\n*************************************************************\n'
   for j in range(0, len(exp.scenarios[i].speedLimits)):
      runSimulation(exp, exp.scenarios[i].period, exp.scenarios[i].speedLimits[j])

   #find fastes Avg time and corresponding speed limit
   # Req: 008, 0010, 0011
   maxCars = max(exp.carsFullyTravel)
   maxCarsSpeedLimit = findSpeedLimit(maxCars, exp.carsFullyTravel)
   print 'The most cars that fully travel the highway is {} when the speed limit is {}Kmph'.format(maxCars, maxCarsSpeedLimit)

   #find fastest special car time and it's speed limit
   # Req 0016, 0017, 0018
   fastSpecialCarTime = findFastSpecialCarTime(exp.specialCarTravelTimes)
   if fastSpecialCarTime is not None:
      print 'The fastest travel time for a car entering at 49 minutes \n after the simulation start is {}Kmph when the speedLimit is {}Kmph'.format(fastSpecialCarTime[0], fastSpecialCarTime[1])
   else:
      print 'No car enter at 49 minutes after the simulation start made it through the highway'

   exp.carsFullyTravel = []
   exp.specialCarTravelTimes = []


      
      
      
   
