from datetime import datetime

import os

from image_acquisition_module import *

############################################################
# SETTINGS
############################################################

#Measurement ID
#Will be used as folder name and prefix for image files
measurementId = "HandsOnDeck" 


#Measurement parameters
temperatureSamplingTime = 300 # seconds
imageSamplingTime = 7200#1800# seconds
numImages =800


#Temperature and image tracking
outputFile = "data.csv"

############################################################
# INITIALIZATION
############################################################

imagesTaken = 0

dataBuffer = []

lastTemperatureTime = datetime.fromtimestamp(0)
lastImageTime = datetime.fromtimestamp(0)

measurementDir=os.path.dirname(os.path.realpath(__file__))+"/"

clearCommand = ["--folder", "/store_00010001/DCIM/103D3200", \
                "-R", "--delete-all-files"]



############################################################
# Time series acquisition
############################################################

while measurementId == "":
    userinput = input('Name the measurement\n')
    measurementId = "".join(c for c in userinput if c.isalpha() or c.isdigit() or c == '_')

CreateMeasurementFolder(measurementId, measurementDir)
outputFile = "data_"+measurementId+".csv"

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(18, GPIO.OUT)

killGphotoProcess()
setCameraConfig()
gp(clearCommand)

temperatureSensors = find_sensors()

# MEASUREMENT
while imagesTaken < numImages:
    timenow = datetime.now()
    temperatureSeconds = (timenow - lastTemperatureTime).total_seconds()
    imageSeconds = (timenow - lastImageTime).total_seconds()
    
    if temperatureSeconds > temperatureSamplingTime:
        MeasureTemperature(timenow)
        ReportStatus(timenow)
    
    if imageSeconds > imageSamplingTime:
        CreatePhoto(timenow)
        imagesTaken += 1
            
            
