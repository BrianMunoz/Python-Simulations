""" Amusement Park """
from random import expovariate, seed, random, gauss, randint
from SimPy.Simulation import *


## @package AmusmentPark
# This package satisfies the requirements of WSUTraffic
# As started in Requirements.docx
MAX_LINE_CAPACITY = 50
SIM_STEP_TIME = 1.0
SIM_DURATION = 720
class Model:
   def __init__(self):
      self.areaA = [
         Ride('Ride A0', 4), Attraction('Attraction A0', 4), Ride('Ride A1', 4),
         Ride('Ride A2', 4), Attraction('Attraction A1', 4), Ride('Ride A3', 4),
         Vendor('Vendor A0', 4), Attraction('Attraction A3', 4), Vendor('Vendor A2', 4)
         ]
      self.areaB = [
         Ride('Ride B0', 4), Attraction('Attraction B0', 20), Ride('Ride B1', 4),
         Ride('Ride B2', 4), Attraction('Attraction B1', 4), Ride('Ride B3', 4),
         Vendor('Vendor B0', 4), Attraction('Attraction B3', 4), Vendor('Vendor B2', 4)
         ]
      self.areaC = [Ride('Ride C1', 4), Attraction('Attraction C1', 4), Vendor('Vendor C1', 4)]
      self.totalDepartures = 0
      self.totalArrived = 0
                    
## Park
# Park object is responsuble for genrating people
# and incrementing the sim time.
class Park(Process):
   def __init__(self):
      Process.__init__(self)
      self.patrons = []
      self.departureTimes = [ 180.0, 240.0, 300.0, 360.0, 420.0, 480.0, 540.0, 600.0, 660.0, 720.0 ]

   def generateAllPatrons(self, model):
      for i in range(1000):
         name = 'person %s' % i
         departureTime = 0
         #decide departure times based on percantage of total patrons.
         if i <= 10:
            departureTime = 180.0
         elif i > 10 and i <= 30:
            departureTime = 240.0
         elif i > 30 and i <= 60:
            departureTime = 300.0
         elif i > 60 and i <= 100:
            departureTime = 360.0
         elif i > 100 and i <= 200:
            departureTime = 420.0
         elif i > 200 and i <= 300:
            departureTime = 480.0
         elif i > 300 and i <= 350:
            departureTime = 540.0
         elif i > 350 and i <= 450:
            departureTime = 600.0
         elif i > 450 and i <= 550:
            departureTime = 660.0
         elif i > 550 and i < 999:
            departureTime = 720.0
         arrivalTime = random.randint(0, 120)   
         person = Person(model.areaA[6], 'a', model, name, departureTime, arrivalTime )
         self.patrons.append(person)
         
      self.patrons = sorted(self.patrons, key=lambda person: person.arrivalTime)

   ## incrementTime
   # This Process Execution Method (PEM)
   # Increment the sim by person arrival until 12:00.
   # After the 12:00 the PEM increments the sim by SIM_STEP_TIME
   def incrementTime(self, model, monitor):
      self.generateAllPatrons( model)
      arrival = self.patrons.pop(0)
      model.totalArrived += 1
      while 1:
         while arrival.arrivalTime <= now():        
            yield put, arrival, model.areaA[6].line, 1
            if model.areaA[6].line.amount == 0:
                arrival.emptyVenueVisit += 1
            activate(arrival, arrival.getServed(model, monitor))
            
            if len(self.patrons) > 0:
               arrival = self.patrons.pop(0)
               model.totalArrived += 1
         yield hold, self, 1

## Ride
# Wait time is 6 minutess
class Ride:
   def __init__(self, name, popularityRating):
      self.line = Level(capacity=MAX_LINE_CAPACITY, name=name, initialBuffered = 0,
                        unitName='people', getQType=FIFO, putQType=FIFO,
                        monitored=True, monitorType=Monitor)
      self.name = name
      self.popularityRating = popularityRating
      self.waitTime = 6
      
## Attraction
# Wait time is 10 
class Attraction:
   def __init__(self, name, popularityRating):
      self.line = Level(capacity=MAX_LINE_CAPACITY, name=name, initialBuffered = 0,
                        unitName='people', getQType=FIFO, putQType=FIFO,
                        monitored=True, monitorType=Monitor)
      self.name = name
      self.popularityRating = popularityRating
      self.waitTime = 10

## Vendor
# Wait time is 3 minutes
class Vendor:
   def __init__(self, name, popularityRating):
      self.line = Level(capacity=MAX_LINE_CAPACITY, name=name, initialBuffered = 0,
                        unitName='people', getQType=FIFO, putQType=FIFO,
                        monitored=True, monitorType=Monitor)
      self.name = name
      self.popularityRating = popularityRating
      self.waitTime = 3

## Person
# This process models a person. A person can wait in line. When a specfic
# person becomes the head of the queue the PEM enjoyVenue is called.
class Person(Process):
      def __init__(self, currentVenue, currentArea, model, name, departureTime, arrivalTime):
         Process.__init__(self)
         self.numVenuesVisted = 1
         self.currentVenue = currentVenue
         self.currentArea = currentArea
         self.name = name
         self.model = model
         self.numVenuesVisited = 0
         self.arrivalTime = arrivalTime
         self.departureTime = departureTime
         self.maxWait = 0
         self.lastVenueEnterTime = arrivalTime #since they all enter A0 first, initialize to arrival time
         self.emptyVenueVisit = 0
         
      def findProbablity(self, area):
         currentProb = []
         maxProb = []
         for i in range(len(area)):
            if i == 0:
               if area[i].line.amount == MAX_LINE_CAPACITY:
                  currentProb.append(0)
                  currentProb.append(area[i])
               else:
                  currentProb.append(expovariate(1.0/area[i].popularityRating))
                  currentProb.append(area[i])
               maxProb = currentProb
            else:
               if area[i].line.amount == MAX_LINE_CAPACITY:
                  decision = 0
               else:
                  decision = expovariate(1.0/area[i].popularityRating)
               currentProb.append(decision)
               currentProb.append(area[i])
               if currentProb[0] > maxProb[0]:
                  maxProb = currentProb
               currentProb = []

         return maxProb

      def findNextVenue(self, monitors):
         repeatVenue = randint(1, 101)
         if repeatVenue >= 95 and self.currentVenue.line.amount != MAX_LINE_CAPACITY:
            return [self.currentVenue,self.currentArea]
         

         areaAChoice = self.findProbablity(self.model.areaA)
         areaBChoice = self.findProbablity(self.model.areaB)
         areaCChoice = self.findProbablity(self.model.areaC)
         maxChoice = max([areaAChoice[0],areaBChoice[0], areaCChoice[0]])

         if maxChoice == 0:
            monitors[3].observe(0)
         else:
            monitors[4].observe(0)
            
         if maxChoice == areaAChoice[0]:
            return [areaAChoice[1],'a']
         elif maxChoice == areaBChoice[0]:
            return [areaBChoice[1],'b']
         else:
            return [areaCChoice[1],'c']

      
         
      ## getServed
      # This Process Execution Method (PEM)
      # gets the lead person from the line and holds
      # it for the wait time associated with the venue
      # Finds the next venue the 
      def getServed(self, model, monitors):
         while 1:
            if now() == 360.0:
               total = model.areaC[0].line.amount + model.areaC[1].line.amount + model.areaC[2].line.amount
               monitors[6].observe(total)
         
            yield get, self, self.currentVenue.line, 1
            lineWait = now() - self.lastVenueEnterTime
            monitors[1].observe(lineWait)
            if lineWait > self.maxWait:
               self.maxWait = lineWait
               monitors[0].observe(self.maxWait)
            yield hold, self, self.currentVenue.waitTime
            self.numVenuesVisited += 1
            
            
            if now() >= self.departureTime:
               model.totalDepartures += 1
               monitors[2].observe(self.numVenuesVisited)
               monitors[5].observe(self.emptyVenueVisit)
               break

            venueAndArea = self.findNextVenue(monitors);
            self.currentVenue = venueAndArea[0]

            if self.currentVenue.line.amount == 0:
               self.emptyVenueVisit += 1
               
            wait = 0
            if self.currentArea != venueAndArea[1]:
               wait = 5
               self.currentArea = venueAndArea[1]
            else:
               wait = 2
               
            self.lastVenueWait = now()
            yield put, self, self.currentVenue.line, 1
            yield hold, self, wait

def findAverageEmptyTime(lineMonitor):
   hits = 0.0
   time = 0.0
   yseries = lineMonitor.yseries()
   tseries = lineMonitor.tseries()
   for i in range(lineMonitor.count()):
      if yseries[i] == 0:
         hits += 1.0
         time += tseries[i]
   return time/hits

def run():
   initialize()
   model = Model()
   park = Park()
   monitors = [Monitor(), Monitor(), Monitor(), Monitor(), Monitor(), Monitor(), Monitor()]
   activate(park, park.incrementTime(model, monitors))
   
   simulate(until = 720.0)
   
   print 'The longest wait time is %s' % max(monitors[0].yseries())
   print 'The average wait per person is %s' % monitors[1].mean()
   print 'The average number of venues visited per day is %s' % monitors[2].mean()
   print 'The maximum number of venues visited is %s' % max(monitors[2].yseries())
   emptyProb = monitors[3].count() / (monitors[3].count() + monitors[4].count())
   epmytProb = emptyProb * 100
   print 'The probability a person will not find a below capacity line is %s ' % emptyProb
   print 'The average number of empty venues visited is %s' % monitors[5].mean()
   emptyAvg = findAverageEmptyTime(model.areaA[6].line.bufferMon)
   print 'The average amount of time vendor A0 is empty is %s' % emptyAvg
   print 'The number of people in areaC at 4:00 is %s' % monitors[6].yseries()[0]
      

run()
