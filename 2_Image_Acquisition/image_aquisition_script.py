from datetime import datetime
import os
from PIL import Image
import PIL #Install pillow
import subprocess
from sh import gphoto2 as gp #Install using apt
from time import sleep
import RPi.GPIO as GPIO # /boot/firmware/config.txt last lines: //dtoverlay=w1-gpio, gpiopin=2//dtoverlay=w1-gpio, gpiopin=3//dtoverlay=w1-gpio, gpiopin=4
#dtoverlay=w1-gpio, gpiopin=2, gpiopin=3, gpiopin=4

from w1thermsensor import W1ThermSensor, Sensor #Install using apt
import adafruit_dht as Adafruit_DHT #pip3 install Adafruit_DHT --install-option="--force-pi"


#REMEMBER TO SET EXPERIMENT NAME!!!!!!!!
measurementId = "HandsOnDeck"

temperatureSamplingTime = 300#300   # seconds
imageSamplingTime = 7200#1800        # seconds
numImages =800#700#350

imagesTaken = 0

lastTemperatureTime = datetime.fromtimestamp(0)
lastImageTime = datetime.fromtimestamp(0)

dataBuffer = []

outputFile = "data.csv"
clearCommand = ["--folder", "/store_00010001/DCIM/103D3200", \
                "-R", "--delete-all-files"]

def killGphotoProcess():
    p =subprocess.Popen(['ps', '-A'], stdout=subprocess.PIPE)
    out,err = p.communicate()
    
    for line in out.splitlines():
        if b'gvfsd-gphoto2' in line:
            pid = int(line.split(None, 1)[0])
            os.system("sudo kill %s" % (pid,))
            #os.kill(pid, signal.SIGKILL)
            
def captureImage():
    gp(["--trigger-capture"])
    sleep(5) # wait with the next capture, so there's time to save the previous one(3 sec was too short once)
    gp(["--get-all-files"])
    gp(clearCommand)
    
def renameFiles(shotTime):
    for filename in os.listdir("."):
        if len(filename) < 13:
            if filename.endswith(".JPG"):
                os.rename(filename, (shotTime+".JPG"))
                print("Renamed the JPG")
    
def setCameraConfig():
    gp(['--set-config', 'iso=100'])
    gp(['--set-config', 'f-number=f/22'])
    gp(['--set-config', 'shutterspeed=2,0000s'])
    gp(['--set-config', 'whitebalance=2']) #Fluorescent
    gp(['--set-config', 'capturetarget=1'])
    gp(['--set-config', 'autofocus=Off'])
    gp(['--set-config', 'imagesize=0']) # 0 - largest, 2 - smallest
    gp(['--set-config', 'exposurecompensation=15']) # off
    #gp(['--set-config', 'imagequality="JPEG Basic"']) # Normal/Basic/Fine currently breaks code
    gp(['--set-config', 'capturemode=0']) # Single Shot
def ToggleLight(on):
    #print("Lights turned " + ("on" if on else "off"))
    GPIO.output(18, on)
    
def AppendBufferToFile():
    global dataBuffer
    global outputFile
    
    file = open(outputFile, "a")
    
    for line in dataBuffer:
        file.write("\t".join(map(str,line))+"\n")
        
    dataBuffer = []
    file.close()

def MeasureTemperature(timenow):
    global temperatureSensors
    global imagesTaken
    Data = [timenow.strftime("%Y-%m-%d %H:%M:%S"), imagesTaken]
    try:
        print(len(temperatureSensors))
        Data.append(read_temp(temperatureSensors[0]))
        #Data.append(read_temp(temperatureSensors[1]))
        #print(read_temp(temperatureSensors[0]))
            
        dht_measurement = Adafruit_DHT.read(Adafruit_DHT.AM2302, 3)
        #print(len(dht_measurement))
        Data.append(dht_measurement[1])
        Data.append(dht_measurement[0])
        
    except Exception as error:
        print("Temp meres hiba!")
        print("An error occurred:", type(error).__name__, ':',error) # An error occurred: NameError
        Data.append([0, 0, 0, 0])
    
    global lastTemperatureTime
    lastTemperatureTime = datetime.now()
    
    global dataBuffer
    dataBuffer.append(Data)
    
def CreatePhoto(timenow):
    ToggleLight(True)
    sleep(1)
    captureImage()
    renameFiles(timenow.strftime("%Y-%m-%d %H:%M:%S"))
    ToggleLight(False)
    
    global lastImageTime
    lastImageTime = datetime.now()
    
    AppendBufferToFile()
    
def CreateMeasurementFolder(measurementId, measurementDir=""):
    if measurementDir =="":
        save_location = "/home/usr/Desktop/Photos/measurements/" + measurementId
    else:   
        save_location = measurementDir + measurementId
        
    try:
        os.makedirs(save_location)
        print("Save folder created")
        
    except:
        print("Failed to create new directory")
    
    os.system("cp "+__file__+" " + save_location + "/code.py")
    os.chdir(save_location)
    print(save_location)

def find_sensors():
    sensors = []
    for sensor in W1ThermSensor.get_available_sensors():
        if sensor.type == Sensor.DS18B20:
            sensors.append(sensor)
    return sensors

def read_temp(sensor):
    temp_C = sensor.get_temperature()
    return temp_C

def ReportStatus(timenow):
    print("###################################################")
    print("Status at " + timenow.strftime("%Y-%m-%d %H:%M:%S"))
    
    global imagesTaken
    global numImages
    print(str(imagesTaken) + " out of " + str(numImages) + " images taken")
    
    global dataBuffer
    lastLine = dataBuffer[-1]
    try:
        print("Temperatures: " + str(lastLine[2]) + " °C, " + str(lastLine[3]) + " °C, " + str(lastLine[4]) + " °C")
        print("Humidity: "+ str(lastLine[5]) + "%")
    except:
        print("Error in temperature print")
############################################################
# INITIALIZE MEASUREMENT

measurementDir=os.path.dirname(os.path.realpath(__file__))+"/"

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
            
            
