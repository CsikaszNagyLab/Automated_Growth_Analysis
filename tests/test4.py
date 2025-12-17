import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import analyzePlate

if __name__ == "__main__":
    json_path = "./tests/files/test3.json"
    configuration = analyzePlate.read_configuration(json_path)

    image_path = "./tests/files/LAST.JPG"
    image = analyzePlate.read_image(image_path, configuration)
    #analyzePlate.show_image(image, "Grayscale Image")

    image = analyzePlate.equalize_light(image, configuration)

    plateRoi = analyzePlate.get_plate_roi(image, 0, configuration)

    overlayed = analyzePlate.self_merge(plateRoi)

    for colonyId in range(len(configuration.plates[0].colony_locations)):
        colonyROI = analyzePlate.get_colony_roi(plateRoi, 0, colonyId, configuration)

        mask = analyzePlate.segment_colony(colonyROI, configuration)
        
        overlayed = analyzePlate.add_colony_mask_to_plate(overlayed, mask, 0, colonyId, configuration)

    analyzePlate.show_image(overlayed, "Plate ROI")