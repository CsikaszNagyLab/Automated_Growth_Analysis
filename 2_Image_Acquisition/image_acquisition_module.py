from datetime import datetime
import os
from PIL import Image
import PIL #Install pillow
import subprocess
from sh import gphoto2 as gp 
from time import sleep
import RPi.GPIO as GPIO 

from w1thermsensor import W1ThermSensor, Sensor 
import adafruit_dht as Adafruit_DHT 

# Hardware configuration requires /boot/firmware/config.txt to contain:
# dtoverlay=w1-gpio,gpiopin=2
# dtoverlay=w1-gpio,gpiopin=3
# dtoverlay=w1-gpio,gpiopin=4

    
##################################################################################################
##############################Hardware: Lighting and Temperature #################################
##################################################################################################


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


    
def AppendBufferToFile():
    global dataBuffer
    global outputFile
    
    file = open(outputFile, "a")
    
    for line in dataBuffer:
        file.write("\t".join(map(str,line))+"\n")
        
    dataBuffer = []
    file.close()

 
    
def CreatePhoto(timenow):
    ToggleLight(True)
    sleep(1)
    captureImage()
    renameFiles(timenow.strftime("%Y-%m-%d %H:%M:%S"))
    ToggleLight(False)
    
    global lastImageTime
    lastImageTime = datetime.now()
    
    AppendBufferToFile()
    
##################################################################################################
##############################Hardware: Lighting and Temperature #################################
##################################################################################################

def find_sensors():
    sensors = []
    for sensor in W1ThermSensor.get_available_sensors():
        if sensor.type == Sensor.DS18B20:
            sensors.append(sensor)
    return sensors

def read_temp(sensor):
    temp_C = sensor.get_temperature()
    return temp_C

   
def ToggleLight(on):
    #print("Lights turned " + ("on" if on else "off"))
    GPIO.output(18, on)

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


##################################################################################################
####################################### Helper functions #########################################
##################################################################################################

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