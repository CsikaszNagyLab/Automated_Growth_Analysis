# Image Acquisition Script

## Setting up RaspbianOS

1. **Update system**
sudo apt update && sudo apt upgrade -y

2. **Install system packages**
sudo apt install -y gphoto2 python3-w1thermsensor

3. **Install Python packages**
- Install pillow
pip3 install pillow sh

- Install DHT sensor library (requires force-pi flag)
pip3 install Adafruit_DHT --install-option="--force-pi"

- Edit /boot/firmware/config.txt and add at the end:
sudo nano /boot/firmware/config.txt

- dd these lines: (use your pin layout choice)
 "dtoverlay=w1-gpio,gpiopin=2"
 "dtoverlay=w1-gpio,gpiopin=3"
 "dtoverlay=w1-gpio,gpiopin=4"

4. **Reboot to apply changes**
sudo reboot



## Installing and Using the Script
1. Copy image acquisition script files from the project repo:
- image_acquisition_module.py
- acquire_timeseries.py

2. Verify hardware connections using terminal
- Check temperature sensors
"ls /sys/bus/w1/devices/"

- Check camera
"gphoto2 --auto-detect"

3. Configure measurement settings
Edit acquire_timeseries.py to set:
- measurementId: Experiment name
- temperatureSamplingTime: Temperature measurement interval (seconds)
- imageSamplingTime: Image capture interval (seconds)
- numImages: Total number of images to capture

4. Run the script
'python3 acquire_timeseries.py'

5. Follow progress in terminal output!