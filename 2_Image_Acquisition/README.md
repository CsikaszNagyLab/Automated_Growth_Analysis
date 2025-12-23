# Experiment Analysis Workflow Manual

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

5. Copy script file into a directory