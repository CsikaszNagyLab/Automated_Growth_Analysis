import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import analyzePlate

if __name__ == "__main__":
    json_path = "./tests/files/test3.json"
    configuration = analyzePlate.read_configuration(json_path)

    image_path = "./tests/files/LAST.JPG"
    image = analyzePlate.read_image(image_path, configuration)

    image = analyzePlate.equalize_light(image, configuration)

    for plateId in range(len(configuration.plates)):

        plateROI = analyzePlate.get_plate_roi(image, plateId, configuration)

        for colonyId in range(len(configuration.plates[plateId].colony_locations)):
            colonyROI = analyzePlate.get_colony_roi(plateROI, plateId, colonyId, configuration)

            mask = analyzePlate.segment_colony(colonyROI, configuration)
            overlayed = analyzePlate.contour_mask(colonyROI, mask)

            colLoc = configuration.plates[plateId].colony_locations[colonyId]
            plateLoc = configuration.plates[plateId].location
            
            analyzePlate.show_image(overlayed, "Segmented Colony Mask Plate: " + str(plateId) + ", Colony: " + str(colonyId))