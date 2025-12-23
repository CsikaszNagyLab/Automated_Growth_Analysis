import cv2
import numpy as np
import math
import cvHelper
import os

class LightEqualization:
    def __init__(self):
        self.center = [0, 0]
        self.radius = 0

class Configuration:
    def __init__(self):
        self.grayscale_transform = [0.299, 0.587, 0.114]
        self.light_equalization = LightEqualization()
        self.light_equalization.center = [3500, 2500]
        self.light_equalization.radius = 1000
        self.plates = []
        self.colony_threshold = 0.1
        self.threshold_skew = 0.5
        self.circularity_threshold = 0.4

class PlateInfo:
    def __init__(self, id, location, size = [1440, 1000], colony_locations = [], colony_descriptors = [], colony_roi_size = 50):
        self.id = id
        self.location = location
        self.size = size
        self.colony_locations = colony_locations
        self.colony_descriptors = colony_descriptors
        self.colony_roi_size = colony_roi_size

def get_plate_roi(image, plate_id, configuration):
    y_top = configuration.plates[plate_id].location[1]
    y_bottom = configuration.plates[plate_id].location[1] + configuration.plates[plate_id].size[1]
    x_left = configuration.plates[plate_id].location[0]
    x_right = configuration.plates[plate_id].location[0] + configuration.plates[plate_id].size[0]

    y_top = max(0, y_top)
    y_bottom = min(image.shape[0], y_bottom)
    x_left = max(0, x_left)
    x_right = min(image.shape[1], x_right)

    plate_roi = image[y_top:y_bottom, x_left:x_right]
    return plate_roi

def get_colony_roi(image, plate_id, colony_id, configuration):
    colony_location = configuration.plates[plate_id].colony_locations[colony_id]
    colony_roi_size = configuration.plates[plate_id].colony_roi_size

    y_top = max(0, colony_location[1] - colony_roi_size)
    y_bottom = min(image.shape[0], colony_location[1] + colony_roi_size)
    x_left = max(0, colony_location[0] - colony_roi_size)
    x_right = min(image.shape[1], colony_location[0] + colony_roi_size)

    colony_roi = image[y_top:y_bottom, x_left:x_right]
    return colony_roi

def set_colony_roi(image, plate_id, colony_id, configuration, colony_roi):
    colony_location = configuration.plates[plate_id].colony_locations[colony_id]
    colony_roi_size = configuration.plates[plate_id].colony_roi_size

    y_top = max(0, colony_location[1] - colony_roi_size)
    y_bottom = min(image.shape[0], colony_location[1] + colony_roi_size)
    x_left = max(0, colony_location[0] - colony_roi_size)
    x_right = min(image.shape[1], colony_location[0] + colony_roi_size)

    image[y_top:y_bottom, x_left:x_right] = colony_roi

def read_image(image_path, configuration):
    image = cv2.imread(image_path).astype(float) / 255.0
    if image is None:
        raise FileNotFoundError(f"Image not found at path: {image_path}")
    if len(image.shape) == 3 and image.shape[2] == 3:
        b,g,r = cv2.split(image)
        grayImage = b * configuration.grayscale_transform[2] + \
                    g * configuration.grayscale_transform[1] + \
                    r * configuration.grayscale_transform[0]
    return grayImage

def show_image(image, title="Image"):
    max_height = 600
    max_width = 800

    resized_image = cvHelper.resize_to_max_size(image, max_width, max_height)

    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def equalize_light(image, configuration):
    radius = configuration.light_equalization.radius
    blurred_image = image

    downscaled = False

    if radius > 10:
        downscale_factor = pow(2, math.ceil(math.log2(radius / 10)))
        blurred_image = cv2.resize(image, (0, 0), fx=1/downscale_factor, fy=1/downscale_factor)
        radius = int(radius / downscale_factor)
        downscaled = True
    
    blurred_image = cv2.GaussianBlur(blurred_image, (radius * 2 + 1, radius * 2 + 1), 0)
    if downscaled:
        blurred_image = cv2.resize(blurred_image, (0, 0), fx=downscale_factor, fy=downscale_factor)

    return cv2.subtract(blurred_image, image)

def segment_colony(image, configuration):
    if np.issubdtype(image.dtype, np.integer):
        image = image.astype(np.float32) / np.iinfo(image.dtype).max

    # Apply Gaussian filter to smooth the image before thresholding
    image = cv2.GaussianBlur(image, (5, 5), 0)

    maxIntensity = np.max(image)
    minIntensity = max(np.min(image), 0)
    
    if (maxIntensity - minIntensity) < configuration.colony_threshold:
        return np.zeros_like(image)
    threshold_value = minIntensity * (1 - configuration.threshold_skew) + maxIntensity * configuration.threshold_skew
    (_, mask) = cv2.threshold(image, threshold_value, 1, cv2.THRESH_BINARY)

    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    contours, hierarchy = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) > 1:
        largest_contour = max(contours, key=cv2.contourArea)
        mask = np.zeros_like(mask)
        cv2.drawContours(mask, [largest_contour], -1, 1, thickness=cv2.FILLED)
    return mask

def overlay_colony_mask(image, mask, channel = 1):
    if image.shape[2] >= 3:
        overlayed = image.copy()
        overlayed[:, :, channel] = mask
        return overlayed

    if   channel == 0:  # Red
        overlayed = cv2.merge([mask, image, image])
    elif channel == 1:  # Green
        overlayed = cv2.merge([image, mask, image])
    elif channel == 2:  # Blue
        overlayed = cv2.merge([image, image, mask])
    else:
        raise ValueError("Channel must be 0 (Red), 1 (Green), or 2 (Blue)")
    return overlayed

def contour_mask(image, mask, line_thickness = 1):
    mask_int = (mask).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask_int, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if image.dtype == np.float32 or image.dtype == np.float64:
        outlined = (np.clip(image.copy(), 0, 1) * 255).astype(np.uint8)
    else:
        outlined = image.copy()
    if len(outlined.shape) < 3:
        outlined = cv2.merge([outlined, outlined, outlined])  # Convert to 3-channel image
    cv2.drawContours(outlined, contours, -1, (255, 0, 0), thickness=line_thickness)
    return outlined

def add_colony_mask_to_plate(plateRoi, mask, plateId, colonyId, configuration):
    colony_location = configuration.plates[plateId].colony_locations[colonyId]
    colonyRoi = get_colony_roi(plateRoi, plateId, colonyId, configuration)
    
    if mask.shape[1:2] != colonyRoi.shape[1:2]:
        raise ValueError("Mask and colony ROI must have the same dimensions.")
    
    mask_colored = overlay_colony_mask(colonyRoi, mask, channel=1)  # Green channel
    y_top = max(0, colony_location[1] - configuration.plates[plateId].colony_roi_size)
    y_bottom = min(plateRoi.shape[0], colony_location[1] + configuration.plates[plateId].colony_roi_size)
    x_left = max(0, colony_location[0] - configuration.plates[plateId].colony_roi_size)
    x_right = min(plateRoi.shape[1], colony_location[0] + configuration.plates[plateId].colony_roi_size)
    plateRoi[y_top:y_bottom, x_left:x_right] = mask_colored
    return plateRoi

def read_configuration(config_path):
    import json
    with open(config_path, 'r') as file:
        config_data = json.load(file)
    
    configuration = Configuration()
    configuration.grayscale_transform = config_data.get('grayscale_transform', [0.299, 0.587, 0.114])
    light_eq = config_data.get('light_equalization', {})
    configuration.light_equalization.center = light_eq.get('center', [3500, 2500])
    configuration.light_equalization.radius = light_eq.get('radius', 1000)
    
    for plate in config_data.get('plates', []):
        colonies = plate.get('colonies', [])
        colony_locations = [colony['location'] for colony in colonies]
        colony_descriptors = [colony.get('descriptor', '') for colony in colonies]
        plate_info = PlateInfo(
            id=plate['id'],
            location=plate['location'],
            size=plate.get('size', [1440, 1000]),
            colony_locations=colony_locations,
            colony_descriptors=colony_descriptors,
            colony_roi_size=plate.get('colony_roi_size', 50)
        )
        configuration.plates.append(plate_info)
    
    configuration.colony_threshold = config_data.get('colony_threshold', 0.1)
    configuration.threshold_skew = config_data.get('threshold_skew', 0.5)
    
    return configuration

def get_range(image):
    min_val = np.min(image)
    max_val = np.max(image)
    return min_val, max_val

def self_merge(image):
    if len(image.shape) == 3 and image.shape[2] == 3: return image
    return cv2.merge([image, image, image])

def compute_colony_properties(mask):
    area = np.sum(mask)
    if area == 0:
        return 0, 0

    contours, _ = cv2.findContours((mask * 255).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return area, 0

    largest_contour = max(contours, key=cv2.contourArea)
    perimeter = cv2.arcLength(largest_contour, True)

    if perimeter == 0:
        circularity = 0
    else:
        circularity = 4 * math.pi * area / (perimeter * perimeter)

    return area, circularity

class AnalysisResult:
    def __init__(self, image_name, plate_id, colony_id, colony_descriptor, area, circularity):
        self.image_name = image_name
        self.plate_id = plate_id
        self.colony_id = colony_id
        self.colony_descriptor = colony_descriptor
        self.area = area
        self.circularity = circularity
def analyze_single_image(image_path, configuration):
    image = read_image(image_path, configuration)
    image = equalize_light(image, configuration)

    results = []

    for plateId in range(len(configuration.plates)):
        plateROI = get_plate_roi(image, plateId, configuration)

        for colonyId in range(len(configuration.plates[plateId].colony_locations)):
            colonyROI = get_colony_roi(plateROI, plateId, colonyId, configuration)

            mask = segment_colony(colonyROI, configuration)
            area, circularity = compute_colony_properties(mask)
            if area > 0 and circularity > configuration.circularity_threshold:
                colony_descriptor = configuration.plates[plateId].colony_descriptors[colonyId] if colonyId < len(configuration.plates[plateId].colony_descriptors) else f"Colony_{colonyId}"
                results.append(AnalysisResult(os.path.basename(image_path), plateId, colonyId, colony_descriptor, area, circularity))
    return results