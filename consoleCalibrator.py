import cv2
import sys
import os
from enum import Enum
import cvHelper
import numpy as np
import layout

import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter

def moving_average(data, window_radius=5):
    cumsum = float(0)
    cumcount = 0
    result = np.zeros_like(data, dtype=float)
    for i in range(window_radius):
        cumsum += data[i]
        cumcount += 1

    for i in range(len(data)):
        if i + window_radius < len(data):
            cumsum += data[i + window_radius]
            cumcount += 1
        if i - window_radius - 1 >= 0:
            cumsum -= data[i - window_radius - 1]
            cumcount -= 1
        result[i] = cumsum / (cumcount + 1e-5)
    return result

class CalibratorState(Enum):
    INIT = 0
    LOADING_IMAGES = 1
    BASE_IMAGE_SELECTION = 2
    GREYSCALE_TRANSFORM = 3
    PLATE_SEED_LOCATION = 4
    PLATE_ENUMERATION = 5
    PLATE_BORDER_LOCATION = 6
    PLATE_BORDER_REFINEMENT = 11
    FULL_IMAGE_SELECTION = 12
    COLONY_ROI_EXTRACTION = 7
    RESULT_EXPORT = 13
    DONE = 8
    ABORT = 9
    ERROR = 10
    SEGMENTATION_CALIBRATION = 14

class CalibratorStateMachine:
    def __init__(self, folder=None):
        self.state = CalibratorState.INIT
        self.grey_image = None
        self.image_file_names = []

        self.folder = folder
        self.base_image_id = 0
        self.greyscale_strategy = 'default'
        self.equalized_image = None
        self.plate_seed_mask = None
        self.plate_contours = []
        self.seeds = []
        self.plate_rectangles = []
        self.full_image_id = 0
        self.plate_rows = []
        self.plate_cols = []
        self.plate_orientations = []
        self.plate_selected = 0
        self.plate_layout_mapping = []
        self.layouts = []

        self.light_equalization_radius = 30
        self.border_reach_LTRB = [900, 600, 900, 600]  # Left, Top, Right, Bottom
        self.peak_detection_threshold = 25
        self.plate_border_threshold = 0.13
        self.plate_distance_threshold = 400

        self.threshold_skew = 0.2
        self.circularity_threshold = 0.4
        self.colony_threshold = 0.05
        self.colony_roi_radius = 50

        self.default_orientation = 1

        while self.state != CalibratorState.DONE:
            if self.state == CalibratorState.INIT:
                self.state_init()
            elif self.state == CalibratorState.LOADING_IMAGES:
                self.state_loading_images()
            elif self.state == CalibratorState.BASE_IMAGE_SELECTION:
                self.state_base_image_selection()
            elif self.state == CalibratorState.GREYSCALE_TRANSFORM:
                self.state_greyscale_transform()
            elif self.state == CalibratorState.PLATE_SEED_LOCATION:
                self.state_plate_seed_location()
            elif self.state == CalibratorState.PLATE_ENUMERATION:
                self.state_plate_enumeration()
            elif self.state == CalibratorState.PLATE_BORDER_LOCATION:
                self.state_plate_border_location()
            elif self.state == CalibratorState.PLATE_BORDER_REFINEMENT:
                self.state_plate_border_refinement()
            elif self.state == CalibratorState.FULL_IMAGE_SELECTION:
                self.state_full_image_selection()
            elif self.state == CalibratorState.COLONY_ROI_EXTRACTION:
                self.state_colony_roi_extraction()
            elif self.state == CalibratorState.SEGMENTATION_CALIBRATION:
                self.state_segmentation_calibration()
            elif self.state == CalibratorState.RESULT_EXPORT:
                self.result_export()
            elif self.state == CalibratorState.ABORT:
                print("Calibration aborted by user.")
                break
            elif self.state == CalibratorState.DONE:
                print("Calibration completed successfully.")
            elif self.state == CalibratorState.ERROR:
                print("An error occurred during calibration.")
                break
            else:
                print(f"Unknown state: {self.state}")
                self.state = CalibratorState.ERROR

    def state_init(self):
        print("State: INIT")
        if (self.folder is None or not os.path.isdir(self.folder)):
            self.folder = input("Enter folder path: ")
        else:
            self.state = CalibratorState.LOADING_IMAGES

    def state_loading_images(self):
        print("State: LOADING_IMAGES")
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
        layout_extensions = {'.csv'}

        images = []
        self.layouts = []
        for filename in os.listdir(self.folder):
            if os.path.isfile(os.path.join(self.folder, filename)):
                ext = os.path.splitext(filename)[1].lower()
                if ext in image_extensions:
                    images.append(os.path.join(self.folder, filename))
                elif ext in layout_extensions:
                    curr = layout.Layout(os.path.join(self.folder, filename))
                    if (curr.valid):
                        self.layouts.append(curr)

        print(f"Number of image files in '{self.folder}': {len(images)}")

        if len(images) == 0:
            print("Please give a new folder path.")
            self.folder = None
            self.state = CalibratorState.INIT

        if len(self.layouts) > 0:
            print("Layout files found:")
            for curr in self.layouts:
                print(f"\t{curr.layout_id}")
        else:
            print("No layout files found")

        res = -1
        while True:
            if res == ord('l'):
                inp = input("Enter folder or file: ")
                try:
                    inp_path = inp if os.path.isabs(inp) else os.path.join(self.folder, inp)
                    if os.path.isfile(inp):
                        files = [inp_path]
                    else:
                        files = []
                        for filename in os.listdir(inp_path):
                            curr_path = os.path.join(inp_path, filename)
                            if os.path.isfile(curr_path):
                                ext = os.path.splitext(filename)[1].lower()
                                if ext in layout_extensions:
                                    files.append(curr_path)
                    for curr_file in files:
                        lay = layout.Layout(curr_file)
                        if lay.valid and not any([x.layout_id == lay.layout_id for x in self.layouts]):
                            self.layouts.append(lay)
                except:
                    print(f"Invalid path (relative paths start from {self.folder})")
            if res == ord('q'):
                self.state = CalibratorState.ABORT
                break
            if res == ord('a'):
                self.image_file_names = images
                self.state = CalibratorState.BASE_IMAGE_SELECTION
                self.full_image_id = len(images) - 1
                break

            print("a - continue")
            print("l - add new layout")
            print("q - quit")

            status_img = np.zeros((200, 400, 3), dtype=np.uint8)
            cv2.putText(status_img, "a - continue", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(status_img, "l - add new layout", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(status_img, "q - quit", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.imshow("Status", status_img)
            res = cv2.waitKey(0)
            cv2.destroyAllWindows()
        
    def state_base_image_selection(self):
        print("State: BASE IMAGE SELECTION")

        image = cv2.imread(self.image_file_names[self.base_image_id])
        if image is None:
            print(f"Error: Could not read image at {self.image_file_names[self.base_image_id]}")
            self.state = CalibratorState.ERROR
            return
        
        print(f"Displaying image: {self.image_file_names[self.base_image_id]}")
        print("Available actions:")
        print("\ta - accept current and continue")
        print("\tn - next image")
        print("\tp - previous image")
        print("\ti - select image by number")
        print("\tq - quit")

        smallImage = cvHelper.resize_to_max_size(image, max_width=800, max_height=600)

        winName = "Base Image Selection"
        cv2.imshow(winName, smallImage)
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        if response == ord('a'):
            print(f"Base image selected: {self.image_file_names[self.base_image_id]}")
            self.state = CalibratorState.FULL_IMAGE_SELECTION
        elif response == ord('n'):
            self.base_image_id = (self.base_image_id + 1) % len(self.image_file_names)
            self.state = CalibratorState.BASE_IMAGE_SELECTION
        elif response == ord('p'):
            self.base_image_id = (self.base_image_id - 1) % len(self.image_file_names)
            self.state = CalibratorState.BASE_IMAGE_SELECTION
        elif response == ord('i'):
            raw_in = input(f"Image number (out of {len(self.image_file_names)}): ")
            try:
                self.base_image_id = int(raw_in) - 1
                if self.base_image_id < 0 or self.base_image_id >= len(self.image_file_names):
                    print("Invalid image number.")
                    self.base_image_id = 0
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
            self.state = CalibratorState.BASE_IMAGE_SELECTION
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def state_full_image_selection(self):
        print("State: FULL IMAGE SELECTION")
        
        image = cv2.imread(self.image_file_names[self.full_image_id])
        if image is None:
            print(f"Error: Could not read image at {self.image_file_names[self.full_image_id]}")
            self.state = CalibratorState.ERROR
            return
        
        print(f"Displaying image: {self.image_file_names[self.full_image_id]}")
        print("Available actions:")
        print("\ta - accept current and continue")
        print("\tn - next image")
        print("\tp - previous image")
        print("\tk - back to base image selection")
        print("\tq - quit")
        
        smallImage = cvHelper.resize_to_max_size(image, max_width=800, max_height=600)
        
        winName = "Full Image Selection"
        cv2.imshow(winName, smallImage)
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if response == ord('a'):
            print(f"Full image selected: {self.image_file_names[self.full_image_id]}")
            self.state = CalibratorState.GREYSCALE_TRANSFORM
        elif response == ord('n'):
            self.full_image_id = (self.full_image_id + 1) % len(self.image_file_names)
            self.state = CalibratorState.FULL_IMAGE_SELECTION
        elif response == ord('p'):
            self.full_image_id = (self.full_image_id - 1) % len(self.image_file_names)
            self.state = CalibratorState.FULL_IMAGE_SELECTION
        elif response == ord('i'):
            raw_in = input(f"Image number (out of {len(self.image_file_names)}): ")
            try:
                self.full_image_id = int(raw_in) - 1
                if self.full_image_id < 0 or self.full_image_id >= len(self.image_file_names):
                    print("Invalid image number.")
                    self.full_image_id = 0
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
            self.state = CalibratorState.FULL_IMAGE_SELECTION
        elif response == ord('k'):
            self.state = CalibratorState.BASE_IMAGE_SELECTION
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def state_greyscale_transform(self):
        image = cv2.imread(self.image_file_names[self.base_image_id])

        print("Select greyscale transform strategy (current: {}):".format(self.greyscale_strategy))
        print("a - accept current and continue")
        print("d - default (NTSC formula)")
        print("r - red channel")
        print("g - green channel")
        print("b - blue channel")
        print("k - back to base image selection")
        print("q - quit")

        weights = cvHelper.grayscale_strategy(self.greyscale_strategy)

        b, g, r = cv2.split(image)
        gray_image = b * weights[2] + g * weights[1] + r * weights[0]
        gray_image = gray_image.round().astype('uint8')

        cv2.imshow("Greyscale Transform", cvHelper.resize_to_max_size(gray_image, max_width=800, max_height=600))
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()
        
        if response == ord('d'):
            self.greyscale_strategy = 'default'
        elif response == ord('r'):
            self.greyscale_strategy = 'red'
        elif response == ord('g'):
            self.greyscale_strategy = 'green'
        elif response == ord('b'):
            self.greyscale_strategy = 'blue'
        elif response == ord('k'):
            self.state = CalibratorState.BASE_IMAGE_SELECTION
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT
        elif response == ord('a'):
            print(f"Greyscale transform accepted: {self.greyscale_strategy}")
            self.grey_image = gray_image
            self.state = CalibratorState.PLATE_SEED_LOCATION
    
    def state_plate_seed_location(self):
        print("State: PLATE SEED LOCATION")
        if self.grey_image is None:
            print("Error: No greyscale image available. Please select a base image first.")
            self.state = CalibratorState.ERROR
            return
        
        print("Current parameters:")
        print(f"\tLight equalization radius: {self.light_equalization_radius}")
        print(f"\tPlate border threshold: {self.plate_border_threshold}")
        print(f"\tPlate distance threshold: {self.plate_distance_threshold}")
        print("Available actions:")
        print("\ta - accept current and continue")
        print("\tl - change light equalization radius")
        print("\tb - change plate border threshold")
        print("\td - change plate distance threshold")
        print("\tk - back to greyscale transform ")
        print("\tq - quit")

        strel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (self.light_equalization_radius * 2 + 1, self.light_equalization_radius * 2 + 1))
        
        light_equalized = cv2.subtract(self.grey_image, cv2.morphologyEx(self.grey_image, cv2.MORPH_OPEN, strel))
        light_equalized = cv2.max(light_equalized.astype(float) / light_equalized.max(), 0)

        mask = light_equalized > self.plate_border_threshold

        distance_transform = cv2.distanceTransform(1 - mask.astype(np.uint8), cv2.DIST_L2, 5)

        plate_seed_mask = distance_transform > self.plate_distance_threshold

        grey_disp = cv2.normalize(self.grey_image, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        light_eq_disp = cv2.normalize(light_equalized, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        mask_disp = (mask * 255).astype(np.uint8)
        plate_seed_disp = (plate_seed_mask * 255).astype(np.uint8)

        # Stack images horizontally
        top_row = np.hstack([grey_disp, light_eq_disp])
        bottom_row = np.hstack([mask_disp, plate_seed_disp])
        mosaic = np.vstack([top_row, bottom_row])

        cv2.imshow("Mosaic: [Grey | LightEq]\n[Mask | PlateSeed]", cvHelper.resize_to_max_size(mosaic, max_width=800, max_height=600))
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if response == ord('l'):
            new_radius = input("Enter new light equalization radius (current: {}): ".format(self.light_equalization_radius))
            try:
                new_radius = int(new_radius)
                if new_radius < 0:
                    print("Radius must be non-negative.")
                else:
                    self.light_equalization_radius = new_radius
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        elif response == ord('b'):
            new_threshold = input("Enter new plate border threshold (current: {}): ".format(self.plate_border_threshold))
            try:
                new_threshold = float(new_threshold)
                if new_threshold < 0 or new_threshold > 1:
                    print("Threshold must be in the range [0, 1].") 
                else:
                    self.plate_border_threshold = new_threshold
            except ValueError:
                print("Invalid input. Please enter a valid float.")
        elif response == ord('d'):
            new_distance = input("Enter new plate distance threshold (current: {}): ".format(self.plate_distance_threshold))
            try:
                new_distance = float(new_distance)
                if new_distance < 0:
                    print("Distance threshold must be non-negative.")
                else:
                    self.plate_distance_threshold = new_distance
            except ValueError:
                print("Invalid input. Please enter a valid float.")
        elif response == ord('a'):
            print("Plate seed location parameters accepted.")
            self.equalized_image = light_equalized
            self.plate_seed_mask = plate_seed_mask

            contours, hierarchy = cv2.findContours(plate_seed_mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Remove contours that touch image borders
            height, width = plate_seed_mask.shape
            filtered_contours = []
            for contour in contours:
                if len(contour) == 0:
                    continue
                contour_points = contour.reshape(-1, 2)
                if np.any(contour_points[:, 0] <= 0) or np.any(contour_points[:, 0] >= width - 1) or \
                   np.any(contour_points[:, 1] <= 0) or np.any(contour_points[:, 1] >= height - 1):
                    continue
                filtered_contours.append(contour)
            contours = filtered_contours

            contours = sorted(contours, key=lambda cnt: cv2.boundingRect(cnt)[1])

            startIndex = 0
            while startIndex < len(contours):
                endIndex = startIndex
                while endIndex + 1 < len(contours) and abs(cv2.boundingRect(contours[endIndex + 1])[1] - cv2.boundingRect(contours[startIndex])[1]) < self.peak_detection_threshold * 2:
                    endIndex += 1
                group = contours[startIndex:endIndex + 1]
                group = sorted(group, key=lambda cnt: cv2.boundingRect(cnt)[0])
                contours[startIndex:endIndex + 1] = group
                startIndex = endIndex + 1

            contours = list(contours)
            if len(contours) == 0:
                print("No plate contours found. Please adjust parameters.")
                return
            self.plate_contours = contours
            
            self.state = CalibratorState.PLATE_ENUMERATION
        elif response == ord('k'):
            self.state = CalibratorState.GREYSCALE_TRANSFORM
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def state_plate_enumeration(self):
        print("State: PLATE ENUMERATION")

        if self.equalized_image is None:
            print("Error: No equalized image available. Please select a plate seed location first.")
            self.state = CalibratorState.ERROR
            return
        print("Available actions:")
        print("\ta - accept current and continue")
        print("\tr - remove plate")
        print("\tk - back to plate seed location")
        print("\tq - quit")
        
        # Create a color image from the plate seed mask
        mask_disp = (self.plate_seed_mask * 255).astype(np.uint8)
        color_img = cv2.cvtColor(mask_disp, cv2.COLOR_GRAY2BGR)

        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 5
        thickness = 8
        color = (0, 0, 255)  # Red in BGR

        seeds = []

        for idx, contour in enumerate(self.plate_contours):
            if len(contour) == 0:
                continue
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / (M["m00"] + 1e-5))
                cy = int(M["m01"] / (M["m00"] + 1e-5))
                cv2.putText(color_img, str(idx + 1), (cx, cy), font, font_scale, color, thickness, cv2.LINE_AA)
                seeds.append((cx, cy))

        cv2.imshow("Plate Enumeration", cvHelper.resize_to_max_size(color_img, max_width=800, max_height=600))
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if response == ord('a'):
            print("Plate enumeration accepted.")
            self.seeds = seeds
            self.state = CalibratorState.PLATE_BORDER_LOCATION
        elif response == ord('r'):
            remove_idx = input("Enter plate index to remove: ")
            try:
                remove_idx = int(remove_idx) - 1
                if 0 <= remove_idx < len(self.plate_contours):
                    self.plate_contours.pop(remove_idx)
                    print(f"Removed plate {remove_idx}.")
                else:
                    print("Invalid index.")
            except ValueError:
                print("Invalid input.")
        elif response == ord('k'):
            self.state = CalibratorState.PLATE_SEED_LOCATION
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def state_plate_border_location(self):
        print("State: PLATE BORDER LOCATION")
        if self.equalized_image is None or self.seeds is None:
            print("Error: No equalized image or seeds available. Please select a plate enumeration first.")
            self.state = CalibratorState.ERROR
            return
        
        leftReach = self.border_reach_LTRB[0]
        topReach = self.border_reach_LTRB[1]
        rightReach = self.border_reach_LTRB[2]
        bottomReach = self.border_reach_LTRB[3]
        
        print("Current parameters:")
        print("\tBorder reach on the left: {}".format(leftReach))
        print("\tBorder reach on the top: {}".format(topReach))
        print("\tBorder reach on the right: {}".format(rightReach))
        print("\tBorder reach on the bottom: {}".format(bottomReach))
        print("Available actions:")
        print("\ta - accept seeds and proceed to border refinement")
        print("\tl - change left border reach")
        print("\tt - change top border reach")
        print("\tr - change right border reach")
        print("\tb - change bottom border reach")
        print("\tk - back to plate enumeration")
        print("\tq - quit")

        image_with_borders = cv2.cvtColor((self.equalized_image * 255).astype(np.uint8), cv2.COLOR_GRAY2BGR)

        blurred_image = cv2.GaussianBlur(self.grey_image, (5, 5), 0)
        self.plate_rectangles = []

        for idx, (cx, cy) in enumerate(self.seeds):
            width = blurred_image.shape[0]
            height = blurred_image.shape[1]
            leftRay = blurred_image[cy, max(0, cx - leftReach):cx]
            rightRay = blurred_image[cy, cx:min(height, cx + rightReach)]
            topRay = blurred_image[max(0, cy - topReach):cy, cx]
            bottomRay = blurred_image[cy:min(width, cy + bottomReach), cx]

            left_min_idx = np.argmin(leftRay)
            right_min_idx = np.argmin(rightRay)
            top_min_idx = np.argmin(topRay)
            bottom_min_idx = np.argmin(bottomRay)

            left_border = cx - leftReach + left_min_idx
            right_border = cx + right_min_idx
            top_border = cy - topReach + top_min_idx
            bottom_border = cy + bottom_min_idx

            cv2.rectangle(image_with_borders, (left_border, top_border), (right_border, bottom_border), (0, 255, 0), 5)
            cv2.line(image_with_borders, (max(0, cx - leftReach), cy), (min(height, cx + rightReach), cy), (255, 0, 0), 5)
            cv2.line(image_with_borders, (cx, max(0, cy - topReach)), (cx, min(width, cy + bottomReach)), (255, 0, 0), 5)
            self.plate_rectangles.append((left_border, top_border, right_border, bottom_border))

        cv2.imshow("Plate Border Location", cvHelper.resize_to_max_size(image_with_borders, max_width=800, max_height=600))
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if response == ord('l'):
            new_left = input("Enter new left border reach (current: {}): ".format(leftReach))
            try:
                new_left = int(new_left)
                if new_left < 0:
                    print("Left border reach must be non-negative.")
                else:
                    self.border_reach_LTRB[0] = new_left
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        elif response == ord('t'):
            new_top = input("Enter new top border reach (current: {}): ".format(topReach))
            try:
                new_top = int(new_top)
                if new_top < 0:
                    print("Top border reach must be non-negative.")
                else:
                    self.border_reach_LTRB[1] = new_top
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        elif response == ord('r'):
            new_right = input("Enter new right border reach (current: {}): ".format(rightReach))
            try:
                new_right = int(new_right)
                if new_right < 0:
                    print("Right border reach must be non-negative.")
                else:
                    self.border_reach_LTRB[2] = new_right
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        elif response == ord('b'):
            new_bottom = input("Enter new bottom border reach (current: {}): ".format(bottomReach))
            try:
                new_bottom = int(new_bottom)
                if new_bottom < 0:
                    print("Bottom border reach must be non-negative.")
                else:
                    self.border_reach_LTRB[3] = new_bottom
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
        elif response == ord('a'):
            print("Plate border locations accepted.")
            self.state = CalibratorState.PLATE_BORDER_REFINEMENT
            self.plate_rows = []
            self.plate_cols = []
            for idx, rect in enumerate(self.plate_rectangles):
                self.plate_rows.append(None)
                self.plate_cols.append(None)
                self.plate_orientations.append(-1)
                self.plate_layout_mapping.append(-1)
        elif response == ord('k'):
            self.state = CalibratorState.PLATE_ENUMERATION
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def state_plate_border_refinement(self):
        print("State: PLATE BORDER REFINEMENT")

        print("Adjust plate borders manually.")
        print("\ta - accept current and continue")
        print("\td - set all plate to layout")
        print("\tl - set specific plate to layout")
        print("\tp - select a plate to adjust")
        print("\tk - back to plate border location")
        print("\tq - quit")
        
        image = cv2.imread(self.image_file_names[self.full_image_id])
        smallImage = cvHelper.resize_to_max_size(image, max_width=800, max_height=600)
        ratio = smallImage.shape[1] / image.shape[1]
        for idx, (cx, cy) in enumerate(self.seeds):
            left, top, right, bottom = self.plate_rectangles[idx]
            cv2.rectangle(smallImage, (int(left * ratio), int(top * ratio)), (int(right * ratio), int(bottom * ratio)), (0, 255, 0), 2)
            cv2.putText(smallImage, f"Id: {(idx + 1)}", (int(left * ratio) + 5, int(cy * ratio)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
            layoutText = "No layout selected"
            if self.plate_layout_mapping[idx] >= 0:
                layoutText = self.layouts[self.plate_layout_mapping[idx]].layout_id
            cv2.putText(smallImage, layoutText, (int(left * ratio) + 5, int(cy * ratio) + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)


        cv2.imshow("Plate Manual Adjustment", smallImage)
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if response == ord('p'):
            plate_id = input("Enter plate index to adjust: ")
            if not plate_id.isnumeric() or int(plate_id) < 1 or int(plate_id) > len(self.seeds):
                print("Invalid input")
            else:
                plate_id = int(plate_id) - 1
            left, top, right, bottom = self.plate_rectangles[plate_id]
            selected = input("Select border to adjust (l-left, r-right, t-top, b-bottom): ")
            if selected not in ['l', 'r', 't', 'b']:
                print("Invalid input")
            else:
                diff_value = input("Enter adjustment value (positive or negative integer): ")
                try:
                    diff_value = int(diff_value)
                    if selected == 'l':
                        left = max(0, left - diff_value)
                    elif selected == 'r':
                        right = min(image.shape[1] - 1, right + diff_value)
                    elif selected == 't':
                        top = max(0, top - diff_value)
                    elif selected == 'b':
                        bottom = min(image.shape[0] - 1, bottom + diff_value)
                    if left >= right or top >= bottom:
                        print("Invalid adjustment leading to non-positive width or height. Change ignored.")
                    else:
                        self.plate_rectangles[plate_id] = (left, top, right, bottom)

                except ValueError:
                    print("Invalid input. Please enter a valid integer.")
        elif response == ord('a'):
            print("Manual adjustments accepted.")
            self.state = CalibratorState.COLONY_ROI_EXTRACTION
        elif response == ord('d'):
            for idx, cl in enumerate(self.layouts):
                print(f"{idx + 1}: {cl.layout_id}")
            layoutId = input("Select layout id: ")
            if not layoutId.isnumeric() or int(layoutId) <= 0 or int(layoutId) > len(self.layouts):
                print("Invalid input")
            else:
                for idx, cl in enumerate(self.plate_layout_mapping):
                    self.plate_layout_mapping[idx] = int(layoutId) - 1
        elif response == ord("l"):
            plateId = input("Select plate: ")
            if not plateId.isnumeric() or int(plateId) <= 0 or int(plateId) > len(self.seeds):
                print("Invalid input")
            else:
                plateId = int(plateId) - 1
                for idx, cl in enumerate(self.layouts):
                    print(f"{idx + 1}: {cl.layout_id}")
                layoutId = input("Select layout id: ")
                if not layoutId.isnumeric() or int(layoutId) < 1 or int(layoutId) > len(self.layouts):
                    print("Invalid input")
                else:
                    self.plate_layout_mapping[plateId] = int(layoutId) - 1
        elif response == ord('k'):
            self.state = CalibratorState.PLATE_BORDER_LOCATION
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def state_colony_roi_extraction(self):
        print("State: COLONY ROI EXTRACTION")

        print("Current parameters:")

        weights = cvHelper.grayscale_strategy(self.greyscale_strategy)

        image = cv2.imread(self.image_file_names[self.full_image_id])
        b, g, r = cv2.split(image)
        gray_image = b * weights[2] + g * weights[1] + r * weights[0]
        gray_image = gray_image.round().astype('uint8')

        sigma = 3

        if sigma > 0:
            diff_image = cv2.GaussianBlur(gray_image, (0, 0), sigma)
            diff_image = cv2.absdiff(cv2.GaussianBlur(gray_image, (0, 0), sigma), cv2.GaussianBlur(self.grey_image, (0, 0), sigma))
        else:
            diff_image = cv2.absdiff(gray_image, self.grey_image)

        (left, top, right, bottom) = self.plate_rectangles[self.plate_selected]
        roi = diff_image[top:bottom, left:right]
        colored_roi = image[top:bottom, left:right]

        if (self.plate_rows[self.plate_selected] is None) \
                or (self.plate_cols[self.plate_selected] is None) \
                or (self.plate_orientations[self.plate_selected] < 0):
            rowPeaks, colPeaks = cvHelper.find_row_col_peaks(roi, threshold=self.peak_detection_threshold)
            rowPeaks = [peak for peak in rowPeaks if peak > 0 and peak < roi.shape[0]]
            colPeaks = [peak for peak in colPeaks if peak > 0 and peak < roi.shape[1]]
            
            orientation = self.default_orientation
            self.plate_rows[self.plate_selected] = rowPeaks
            self.plate_cols[self.plate_selected] = colPeaks
            self.plate_orientations[self.plate_selected] = orientation
        else:
            rowPeaks = self.plate_rows[self.plate_selected]
            colPeaks = self.plate_cols[self.plate_selected]
            orientation = self.plate_orientations[self.plate_selected]

        resized = cvHelper.resize_to_max_size(colored_roi, max_width=800, max_height=600)
                
        ratio = resized.shape[1] / roi.shape[1]
        annotated = resized.copy()

        if (len(rowPeaks) * len(colPeaks) > 0):
            for idx, peak in enumerate(rowPeaks):
                cv2.line(annotated, (0, int(peak * ratio)), (annotated.shape[1], int(peak * ratio)), (255, 0, 0), 1)
                cv2.putText(annotated, str(idx + 1), (5, int(peak * ratio) - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)
            for idx, peak in enumerate(colPeaks):
                cv2.line(annotated, (int(peak * ratio), 0), (int(peak * ratio), annotated.shape[0]), (0, 255, 0), 1)
                cv2.putText(annotated, str(idx + 1), (int(peak * ratio) + 5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

            c = 0
            r = 0
            cv2.putText(annotated, cvHelper.get_colony_location_identifier(orientation, c, r, len(colPeaks), len(rowPeaks)), 
                        (int(colPeaks[c] * ratio), int(rowPeaks[r] * ratio)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            c = 0
            r = len(rowPeaks) - 1
            cv2.putText(annotated, cvHelper.get_colony_location_identifier(orientation, c, r, len(colPeaks), len(rowPeaks)), 
                        (int(colPeaks[c] * ratio), int(rowPeaks[r] * ratio)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            c = len(colPeaks) - 1
            r = 0
            cv2.putText(annotated, cvHelper.get_colony_location_identifier(orientation, c, r, len(colPeaks), len(rowPeaks)), 
                        (int(colPeaks[c] * ratio), int(rowPeaks[r] * ratio)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
            c = len(colPeaks) - 1
            r = len(rowPeaks) - 1
            cv2.putText(annotated, cvHelper.get_colony_location_identifier(orientation, c, r, len(colPeaks), len(rowPeaks)), 
                        (int(colPeaks[c] * ratio), int(rowPeaks[r] * ratio)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
        
        else:
            print("WARNING: No rows and/or columns found, consider lowering threshold")

        all_done = all(row is not None for row in self.plate_rows) and all(col is not None for col in self.plate_cols)

        print("Available actions:")
        if all_done:
            print("\ta - FINALIZE")
        else:
            print("\ta - accept current plate and continue")
        print("\tn - next plate")
        print("\tp - previous plate")
        print("\tt - modify threshold (currently {})".format(self.peak_detection_threshold))
        print("\tr - remove detected row")
        print("\tc - remove detected column")
        print("\th - flip orientation horizontally")
        print("\tv - flip orientation vertically")
        print("\tf - flip orientation rows/columns")
        print("\tu - flip 180 degrees")
        print("\tk - back to full image selection")
        print("\tq - quit")

        cv2.imshow(f"Plate {self.plate_selected} ROI", annotated)
        cv2.namedWindow(f"Plate {self.plate_selected} ROI")
        res = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if res == ord('a'):
            if all_done:
                print("All plates processed. Finalizing calibration.")
                self.state = CalibratorState.SEGMENTATION_CALIBRATION
                self.plate_highlighed = 0
            else:
                self.plate_selected = (self.plate_selected + 1) % len(self.plate_rectangles)
                self.state = CalibratorState.COLONY_ROI_EXTRACTION
        elif res == ord('n'):
            self.plate_selected = (self.plate_selected + 1) % len(self.plate_rectangles)
            self.state = CalibratorState.COLONY_ROI_EXTRACTION
        elif res == ord('p'):
            self.plate_selected = (self.plate_selected - 1) % len(self.plate_rectangles)
            self.state = CalibratorState.COLONY_ROI_EXTRACTION
        elif res == ord('t'):
            new_threshold = input("Enter new peak detection threshold (current: {}): ".format(self.peak_detection_threshold))
            try:
                new_threshold = float(new_threshold)
                if new_threshold < 0:
                    print("Threshold must be non-negative.")
                else:
                    self.peak_detection_threshold = new_threshold
                    self.plate_rows[self.plate_selected] = None
                    self.plate_cols[self.plate_selected] = None
            except ValueError:
                print("Invalid input. Please enter a valid float.")
        elif res == ord('r'):
            if len(rowPeaks) == 0:
                print("No rows to remove.")
            else:
                remove_idx = input("Enter row index to remove: ")
                try:
                    remove_idx = int(remove_idx) - 1
                    if 0 <= remove_idx < len(rowPeaks):
                        rowPeaks.pop(remove_idx)
                        self.plate_rows[self.plate_selected] = rowPeaks
                        print(f"Removed row {remove_idx}.")
                    else:
                        print("Invalid index.")
                except ValueError:
                    print("Invalid input.")
        elif res == ord('c'):
            if len(colPeaks) == 0:
                print("No columns to remove.")
            else:
                remove_idx = input("Enter column index to remove: ")
                try:
                    remove_idx = int(remove_idx) - 1
                    if 0 <= remove_idx < len(colPeaks):
                        colPeaks.pop(remove_idx)
                        self.plate_cols[self.plate_selected] = colPeaks
                        print(f"Removed column {remove_idx}.")
                    else:
                        print("Invalid index.")
                except ValueError:
                    print("Invalid input.")
        elif res == ord('h'):
            self.plate_orientations[self.plate_selected] = orientation ^ 0b010
            self.default_orientation = self.plate_orientations[self.plate_selected]
        elif res == ord('v'):
            self.plate_orientations[self.plate_selected] = orientation ^ 0b100
            self.default_orientation = self.plate_orientations[self.plate_selected]
        elif res == ord('f'):
            self.plate_orientations[self.plate_selected] = orientation ^ 0b001
            self.default_orientation = self.plate_orientations[self.plate_selected]
        elif res == ord('u'):
            self.plate_orientations[self.plate_selected] = orientation ^ 0b110
            self.default_orientation = self.plate_orientations[self.plate_selected]
        elif res == ord('k'):
            self.state = CalibratorState.FULL_IMAGE_SELECTION
        elif res == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def state_segmentation_calibration(self):
        print("State: SEGMENTATION CALIBRATION")
        print("Current parameters:")
        print(f"\tThreshold skew: {self.threshold_skew}")
        print(f"\tCircularity threshold: {self.circularity_threshold}")
        print(f"\tColony threshold: {self.colony_threshold}")
        print(f"\tColony ROI radius: {self.colony_roi_radius}")
        print("Available actions:")
        print("\ta - accept current and continue")
        print("\ts - change threshold skew")
        print("\tc - change circularity threshold")
        print("\tt - change colony threshold")
        print("\tr - change colony ROI radius")
        if self.plate_highlighed <= 0 or self.plate_highlighed > len(self.plate_rectangles):
            print("\tp - zoom on plate")
        else:
            print("\tp - back to full image")
        print("\tq - quit")

        image = cv2.imread(self.image_file_names[self.full_image_id])
        weights = cvHelper.grayscale_strategy(self.greyscale_strategy)
        b, g, r = cv2.split(image)
        gray_image = b * weights[2] + g * weights[1] + r * weights[0]
        gray_image = gray_image.round().astype('uint8')

        import analyzePlate
        configuration = analyzePlate.Configuration()
        configuration.grayscale_transform = cvHelper.grayscale_strategy(self.greyscale_strategy)
        configuration.light_equalization.radius = self.light_equalization_radius
        configuration.plates = []
        configuration.colony_threshold = self.colony_threshold
        configuration.threshold_skew = self.threshold_skew
        configuration.circularity_threshold = self.circularity_threshold
        configuration.colony_roi_radius = self.colony_roi_radius
        
        for plate_idx, (left, top, right, bottom) in enumerate(self.plate_rectangles):
            configuration.plates.append(analyzePlate.PlateInfo(plate_idx, [left, top], [right - left, bottom - top], [], [], self.colony_roi_radius))
            
            for rowId, row in enumerate(self.plate_rows[plate_idx]):
                for colId, col in enumerate(self.plate_cols[plate_idx]):
                    configuration.plates[-1].colony_locations.append([col, row])
                    descriptor = self.translate_colony_descriptor(plate_idx, colId, rowId)
                    configuration.plates[-1].colony_descriptors.append(descriptor)

        overlayed_image = analyzePlate.self_merge(gray_image)
        gray_image = analyzePlate.equalize_light(gray_image, configuration)

        for plate_idx, (left, top, right, bottom) in enumerate(self.plate_rectangles):
            roi = gray_image[top:bottom, left:right]
            overlayed = analyzePlate.self_merge(overlayed_image[top:bottom, left:right])
            for colonyId in range(len(configuration.plates[plate_idx].colony_locations)):
                colonyROI = analyzePlate.get_colony_roi(roi, plate_idx, colonyId, configuration)
                mask = analyzePlate.segment_colony(colonyROI, configuration)
                overlayedColony = analyzePlate.contour_mask(analyzePlate.get_colony_roi(overlayed, plate_idx, colonyId, configuration), mask, line_thickness=3)
                analyzePlate.set_colony_roi(overlayed, plate_idx, colonyId, configuration, overlayedColony)

            overlayed_image[top:bottom, left:right] = overlayed

        if self.plate_highlighed > 0 and self.plate_highlighed <= len(self.plate_rectangles):
            left, top, right, bottom = self.plate_rectangles[self.plate_highlighed - 1]
            overlayed_image = overlayed_image[top:bottom, left:right]

        cv2.imwrite("segmentation_calibration_temp.png", overlayed_image)
        resized = cvHelper.resize_to_max_size(overlayed_image, max_width=800, max_height=600)
        cv2.imshow("Segmentation Calibration", resized)
        response = cv2.waitKey(0)
        cv2.destroyAllWindows()

        if response == ord('s'):
            new_skew = input("Enter new threshold skew (current: {}): ".format(self.threshold_skew))
            try:
                new_skew = float(new_skew)
                self.threshold_skew = new_skew
            except ValueError:
                print("Invalid input. Please enter a valid float.")
            self.state = CalibratorState.SEGMENTATION_CALIBRATION
        elif response == ord('c'):
            new_circularity = input("Enter new circularity threshold (current: {}): ".format(self.circularity_threshold))
            try:
                new_circularity = float(new_circularity)
                if new_circularity < 0 or new_circularity > 1:
                    print("Circularity threshold must be in the range [0, 1].")
                else:
                    self.circularity_threshold = new_circularity
            except ValueError:
                print("Invalid input. Please enter a valid float.")
            self.state = CalibratorState.SEGMENTATION_CALIBRATION
        elif response == ord('t'):
            new_threshold = input("Enter new colony threshold (current: {}): ".format(self.colony_threshold))
            try:
                new_threshold = float(new_threshold)
                if new_threshold < 0 or new_threshold > 1:
                    print("Colony threshold must be in the range [0, 1].")
                else:
                    self.colony_threshold = new_threshold
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
            self.state = CalibratorState.SEGMENTATION_CALIBRATION
        elif response == ord('r'):
            new_radius = input("Enter new colony ROI radius (current: {}): ".format(self.colony_roi_radius))
            try:
                new_radius = int(new_radius)
                if new_radius < 1:
                    print("Colony ROI radius must be positive.")
                else:
                    self.colony_roi_radius = new_radius
            except ValueError:
                print("Invalid input. Please enter a valid integer.")
            self.state = CalibratorState.SEGMENTATION_CALIBRATION
        elif response == ord('a'):
            print("Segmentation parameters accepted.")
            self.state = CalibratorState.RESULT_EXPORT
        elif response == ord('p'):
            if self.plate_highlighed <= 0 or self.plate_highlighed > len(self.plate_rectangles):
                input_plate = input("Enter plate index to zoom on: ")
                try:
                    input_plate = int(input_plate)
                    if input_plate < 1 or input_plate > len(self.plate_rectangles):
                        print("Invalid plate index.")
                    else:
                        self.plate_highlighed = input_plate
                except ValueError:
                    print("Invalid input. Please enter a valid integer.")
            else:
                self.plate_highlighed = 0
            self.state = CalibratorState.SEGMENTATION_CALIBRATION
        elif response == ord('q'):
            print("Quitting calibration.")
            self.state = CalibratorState.ABORT

    def translate_colony_descriptor(self, plateId, columnId, rowId):
        rows = len(self.plate_rows[plateId])
        cols = len(self.plate_cols[plateId])
        id = cvHelper.get_colony_location_identifier(self.plate_orientations[plateId], columnId, rowId, cols, rows)
        mapping = self.layouts[self.plate_layout_mapping[plateId]].mapping
        if id in mapping:
            return mapping[id]
        return f"Plate{plateId}_{id}"

    def result_export(self):
        results = {
            "grayscale_transform": cvHelper.grayscale_strategy(self.greyscale_strategy),
            "light_equalization": {"radius" : self.light_equalization_radius, "center" : [0, 0]},
            "threshold_skew" : self.threshold_skew,
            "circularity_threshold": self.circularity_threshold,
            "colony_threshold" : self.colony_threshold,
            "plates": 
            [
                {
                    "id" : "plate{}".format(idx),
                    "location" : [int(left), int(top)],
                    "size" : [int(right - left), int(bottom - top)],
                    "colonies": [{"location" : [int(c), int(r)], 
                                  "location_id": cvHelper.get_colony_location_identifier(self.plate_orientations[idx], colId, rowId, len(self.plate_cols[idx]), len(self.plate_rows[idx])),
                                  "descriptor": self.translate_colony_descriptor(idx, colId, rowId)} 
                                 for rowId, r in enumerate(self.plate_rows[idx]) for colId, c in enumerate(self.plate_cols[idx])]
                    #"colony_locations" : [[int(c), int(r)] for r in self.plate_rows[idx] for c in self.plate_cols[idx]]
                } for idx, (left, top, right, bottom) in enumerate(self.plate_rectangles)
            ]
        }

        output_path = os.path.join(self.folder, "calibration_results.json")
        import json
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=4)
        print(f"Calibration results exported to {output_path}")
        self.state = CalibratorState.DONE


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python consoleCalibrator.py <folder_path>")
        folder_path = None
    else:
        folder_path = sys.argv[1]
    
    machine = CalibratorStateMachine(folder_path)