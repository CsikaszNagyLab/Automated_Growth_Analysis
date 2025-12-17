import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import analyzePlate

if __name__ == "__main__":
    image_path = "./tests/files/LAST.JPG"

    configuration = analyzePlate.Configuration()
    configuration.grayscale_transform = [1, 0, 0]
    configuration.light_equalization.center = [3500, 2500]
    configuration.light_equalization.radius = 150
    configuration.plates.append(analyzePlate.PlateInfo(0, [2145, 2087], [1440, 952], []))
    configuration.plates[0].colony_locations.append([570, 304])
    configuration.colony_roi_size = 50
    configuration.threshold_skew = 0.3
    
    image = analyzePlate.read_image(image_path, configuration)
    #analyzePlate.show_image(image, "Grayscale Image")

    image = analyzePlate.equalize_light(image, configuration)

    plateRoi = analyzePlate.get_plate_roi(image, 0, configuration)
    #analyzePlate.show_image(plateRoi, "Plate ROI")

    colonyRoi = analyzePlate.get_colony_roi(plateRoi, 0, 0, configuration)
    #analyzePlate.show_image(colonyRoi, "Colony ROI")

    colony_mask = analyzePlate.segment_colony(colonyRoi, configuration)
    
    analyzePlate.show_image(analyzePlate.contour_mask(colonyRoi, colony_mask), "Colony Mask Overlay")
    #analyzePlate.show_image(colony_mask, "Colony Mask")