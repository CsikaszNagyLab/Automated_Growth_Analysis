import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import analyzePlate

if __name__ == "__main__":
    image_path = os.path.join(os.path.dirname(__file__), "files", "APPEAR.JPG")

    configuration = analyzePlate.Configuration()
    configuration.grayscale_transform = [1, 0, 0]
    configuration.light_equalization.center = [3500, 2500]
    configuration.light_equalization.radius = 150
    configuration.plates.append(analyzePlate.PlateInfo(0, [2287, 970], [1440, 952], []))
    configuration.plates[0].colony_locations.append([764, 531])
    configuration.plates[0].colony_locations.append([666, 730])
    configuration.colony_roi_size = 50
    configuration.colony_threshold = 0.1
    configuration.threshold_skew = 0.3
    
    image = analyzePlate.read_image(image_path, configuration)
    #analyzePlate.show_image(image, "Grayscale Image")

    image = analyzePlate.equalize_light(image, configuration)

    plateRoi = analyzePlate.get_plate_roi(image, 0, configuration)
    #analyzePlate.show_image(plateRoi, "Plate ROI")

    colony1Roi = analyzePlate.get_colony_roi(plateRoi, 0, 0, configuration)
    colony2Roi = analyzePlate.get_colony_roi(plateRoi, 0, 1, configuration)
    #analyzePlate.show_image(colonyRoi, "Colony ROI")

    colony_mask1 = analyzePlate.segment_colony(colony1Roi, configuration)
    colony_mask2 = analyzePlate.segment_colony(colony2Roi, configuration)

    analyzePlate.show_image(analyzePlate.contour_mask(colony1Roi, colony_mask1), "Colony 1 Mask Overlay")
    analyzePlate.show_image(analyzePlate.contour_mask(colony2Roi, colony_mask2), "Colony 2 Mask Overlay")