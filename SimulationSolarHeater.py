
#Author Jin Gu
#Date 2/28/2022


from aifc import Error


"""
1. Assumptions
(1) The surface temperature of the solar components is uniform and constant;
(2) There is no dirt thermal resistance when hot water flows in the solar collector;
(3) The hot water flow is stable;
(4) The distance between the storage tank and the solar components is ignored;
(5) The heat loss is negligible;
(6) The water only circulates between the collector and the storage tank,
and there is no additional inflow and outflow of water.

divide the system into 4 class :
panel class: receive heat from the solar and heat the water
SolarHeater: has multiple panels heat the water
pumping: used to feed water to heater and add or drop water to tank
tank: store the water ignore the heat loss.

2. This simulation system calculate the temperature of water after one hours heating.
There are some conditions we need to set at first:
(1) initialize the volume of tank as 500L, volume of water as 60L.
(2) set the number of panel as 1.
(3) set the water heat from 15 ℃.
(4) set the density of water as 980 kg/m3, SpecificHeatCapacity: 4.2 kJ/Kg°C
(5) set Incident Energy received from Solar as 1224kj/h/m2(from : https://en.wikipedia.org/wiki/Solar_constant)
(6) RESULT: After one hour's heat: the temperature of water increases from 15 to 18.21
"""


class Fluid:
    # the default fluid is water
    SpecificHeatCapacity = 4.2  # kJ/Kg°C

    # density of hot water , we ignore the density change of water as temperature changes;
    Density = 980  # kg/m3


"""
This class represents the panel of SolarHeater.
Each panel can convert solar energy to thermal used to heat water. We implement key method heatEnergy by Fourier law:
[Q = mc(dT)] to get the dT of water in panel.

"""


# the panel system of heater :
class Panel:

    def __init__(self, height=1, width=1, efficiency=0.18):
        self.height = height
        self.width = width
        self.efficiency = efficiency

    # Calculating the energy get from the solar and the temperature increases of each panel
    # Q the energy of one panel get from the solar in unit time(related to area of panel, convert efficiency
    # and solar radiant energy )
    def tempResult(self, solarEnergy: int, mass: float, temprature: float) -> float:
        # Energy per meter sqr times the efficiency of the panel
        Q = solarEnergy * self.height * self.width * self.efficiency
        return Panel.heatEnergy(Q, mass, Fluid.SpecificHeatCapacity, temprature)

    # Calculating increasing temperature(dT) using Fourier law of Thermal Conduction [Q = mc(dT)]
    # so dT = Q/mc -> t2 = Q/mc + t1 (initial T)
    def heatEnergy(self: float, mass: float, specificHeat: float, temprature) -> float:
        return (self / (mass * specificHeat)) + temprature

    # constructor of panel
    def setSpec(self, height: int = None, width: int = None, efficiency: float = None):
        if (height != None):
            self.height = height
        if (width != None):
            self.width = width
        if (efficiency != None):
            self.efficiency = efficiency


"""
In the SolarHeater class we set the max_heat temperature be 95, cause we have ignored the heat loss so the temperature 
will go up constantly as time passed which will be not "meaningful" if exceed 100;
Obviously, the SolarHeater transfer the Incident Energy received from solar to thermal energy so 
we need to set the Incident Energy received, according to wikipedia the Incident Energy the earth received is 340 W /m2
As we calculate by hour and the area of panel is 1m2 so the Incident energy received per hour : 340 * 3600 = 1224kj/h

In this class, the thermal collector will have multiple panels, so we implement key method heatWater to get the  
temperature of outlet water after heating by all thermal collector. 
At any time, we have the heat balance formula: 
M : sum of water quality
T : outlet temperature
n : number of panels
m : quality of water in panel
t : temperature of water in panel
(Sum)m(each panel's water quality) * T = Total_Q = n(number of panels) * q(thermal of each panel, equals m * t)
which is M*T = n*m*t
we can get outlet Temperature(T) then.
"""


class SolarHeater:
    MAX_HEAT = 95
    __panels = []  # List of Solar Panel

    """
        args:
        numberOfPanels: Define the number of panels required
        customPanels: Any number of custom panels if wanted, remaining number of panels will be created with default number.
    """

    # default constructor
    def __init__(self, numberOfPanels: int, customSpec: tuple() = ()):
        self.buildSolarPanels(numberOfPanels, customSpec)
        self.incidentEnergy = -1

    #
    def buildSolarPanels(self, number, customSpec: tuple()) -> [Panel]:
        if len(customSpec) != 0 and len(customSpec) != 3:
            raise ValueError

        # if we have defined panel, use it, if nor we use default panel
        h, w, e = customSpec if (len(customSpec) == 3) else (1, 1, 0.18)
        for _ in range(number):
            self.__panels.append(Panel(height=h, width=w, efficiency=e))

    # set specific panel of thermal collector
    def changePanelAt(index: int, height: int = None, width: int = None, efficiency: float = None):
        if index >= len(self.panels):
            return
        self.__panels[index].setSpec(height=height, width=width, efficiency=efficiency)

    def getIncidentEnergy(self) -> int:
        if self.incidentEnergy == 0:
            print("Incident energy on solar panel needs to be non-negative")
            raise ValueError

        return self.incidentEnergy

    # set radiant energy of solar
    def setIncidentEnergy(self, energy):
        # default is 1224kj/h
        self.incidentEnergy = energy

    # At any time, we have the heat balance formula:
    # (Sum)m(each panel's water quality) * dT = Total_Q = n(number of panels) * q(thermal of each panel)
    # we can get outlet Temperature then.
    def heatWater(self, volume: int, initialTemp: float) -> float:
        if initialTemp >= self.MAX_HEAT: return self.MAX_HEAT
        # Restricting heating over the max temp

        numberOfPanels = len(self.__panels)
        volumePerPanel = volume / numberOfPanels
        massPerPanel = volumePerPanel * Fluid.Density

        tempObtainedFromPanels = []
        for panel in self.__panels:
            tempObtainedFromPanels.append(
                panel.tempResult(self.incidentEnergy, massPerPanel, initialTemp) * massPerPanel)

        # Weight average of water temperature obtained from all panels
        # Since weight avg can be different for panels of different dimensions
        total_mass = volume * Fluid.Density
        final_temp = sum(tempObtainedFromPanels) / total_mass

        return final_temp


"""
Tank used to store the water and we have the key method __mixWater used to calculate the temperature of water in tank
seem as the heatWater method we have the heat balance formula:
Q: total thermal of water in the system
Qt : thermal of water in tank
Qi : thermal of water from thermal collector
Q = Qt + Qi
By Q = m*t:
M * T = Mt * Tt + Mi + Ti
So we get the T -> system temperature actually is the temperature after adding water(tank's output T )
"""


class Tank:

    def __init__(self, capacity: int = 600, waterVol: int = 200, waterTemp: float = 30):
        self.capacity = capacity  # Volume of tank in Liters
        self.waterVol = waterVol  # Volume of water in Liters
        self.waterTemp = waterTemp  # Uniform water temprature in C

    def setWaterVol(self, volume):
        self.waterVol = volume

    def getWaterVol(self) -> int:
        return self.waterVol

    def addWater(self, volume: int, temprature: int):
        if volume > self.capacity - self.waterVol:
            print("Cannot add more water than the overall tank capacity")
        self.__mixWater(volume, temprature)

    # if we add water to the tank:
    # calculation same as above:
    # the total energy of water contains related to its quality and thermal per unit received/contains:
    # function is: Total_Q = m*T
    # We can get the temperature change per unit of outlet by : Unit_T = Total_Q/Total_M
    def __mixWater(self, volume, temprature):
        self.waterTemp = ((volume * temprature) + (self.waterTemp * self.waterVol)) / (volume + self.waterVol)
        self.waterVol += volume

    def releaseWaterVolume(self, volume):
        if volume > self.waterVol:
            print("Sepcify volume not more than current volume of water\nCurrent Volume of Water:", self.waterCap,
                  " Kg/m3")
            return
        self.waterVol -= volume


"""
We use this class to help get the temperature of the tank and thermal collector 
"""


class Pumping:

    def __init__(self, solar_heater: SolarHeater, tank: Tank, pumpStatus: bool = False, pumpingRate: int = 1):
        self.solar_heater = solar_heater
        self.tank = tank
        self.pumpingRate = pumpingRate  # Liters water transfer per second

    def setPumpingRateLitersPerSec(self, rate):
        self.pumpingRate = rate

    # Use pump to circulate water: add water into the thermal collector from tank
    # return value is water out from the thermal collector after heating
    def feedWaterToSolarHeater(self) -> int:
        return self.solar_heater.heatWater(self.pumpingRate, self.tank.waterTemp)

    def drawWaterFromTank(self):
        self.tank.releaseWaterVolume(self.pumpingRate)

    def feedWaterToTank(self, waterTemperature: int):
        self.tank.addWater(self.pumpingRate, waterTemperature)


class Controller:
    SOLAR_HEATER = 1
    TANK = 2
    PUMPING_SYSTEM = 3

    def __init__(self):
        self.heater = self.componentFactory(self.SOLAR_HEATER)
        self.tank = self.componentFactory(self.TANK)
        self.pump = self.componentFactory(self.PUMPING_SYSTEM, self.heater, self.tank)
        self.targetTemp = self.heater.MAX_HEAT

    # calculate the temperature of water in tank after fixed time of heating
    def __simulateSystemForSeconds(self, time: int):
        timeTaken = 0
        for timeTaken in range(time):
            self.__performOneCycle()
            if (self.tank.waterTemp >= self.targetTemp):
                break
        return timeTaken

    #  time exchange per cycle
    def __performOneCycle(self):
        # first draw water from tank -> water in tank decrease
        self.pump.drawWaterFromTank()
        # get the temp of water after heater
        newWaterTemp = self.pump.feedWaterToSolarHeater()
        # mix the heated water with water in tank and get the new temp of total water
        self.pump.feedWaterToTank(newWaterTemp)

    def simulateSystemForSeconds(self, second: int):
        timeTaken = self.__simulateSystemForSeconds(second)
        print("Temp of water after running the heater for ", timeTaken + 1, "sec ", self.tank.waterTemp, "°C")

    def simulateSystemForHours(self, hours: int):
        timeTaken = self.__simulateSystemForSeconds(hours * 3600)
        hoursTaken = timeTaken / 3600
        print("Temp of water after running the heater for ", hours, "Hours ", self.tank.waterTemp, "°C")

    def componentFactory(self, type, *spec):

        if type == self.SOLAR_HEATER:
            panel = SolarHeater(numberOfPanels=1)
            panel.setIncidentEnergy(1224)
            return panel
        elif type == self.TANK:
            return Tank(capacity=500, waterVol=60, waterTemp=15)
        elif type == self.PUMPING_SYSTEM:
            # spec[0] default thermal collector
            # spec[1] default tank
            pump = Pumping(spec[0], spec[1])
            pump.setPumpingRateLitersPerSec(1)
            return pump
        else:
            raise Error("Please provide a valid option")


def main():
    controller = Controller()
    controller.simulateSystemForHours(1)


if __name__ == "__main__":
    main()
