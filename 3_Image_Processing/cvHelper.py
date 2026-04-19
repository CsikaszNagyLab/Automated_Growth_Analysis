import cv2
import numpy as np

def resize_to_max_size(image, max_width = -1, max_height = -1):
    if max_width <= 0 and max_height <= 0:
        return image
    
    height, width = image.shape[:2]

    if max_height < 0:
        max_height = height
    if max_width < 0:
        max_width = width

    scale = min(max_height / height, max_width / width)
    new_size = (int(width * scale), int(height * scale))
    image = cv2.resize(image, new_size)

    return image

def find_row_col_peaks(roi, threshold=25):
    rowSums = np.sum(roi, axis=1) / roi.shape[1]
    colSums = np.sum(roi, axis=0) / roi.shape[0]

    rowsAboveThreshold = rowSums > threshold
    startsMask = np.logical_and(~rowsAboveThreshold[:-1], rowsAboveThreshold[1:])
    startsMask = np.concatenate(([rowsAboveThreshold[0]], startsMask))
    endsMask = np.logical_and(rowsAboveThreshold[:-1], ~rowsAboveThreshold[1:])
    endsMask = np.concatenate((endsMask, [rowsAboveThreshold[-1]]))

    starts = np.where(startsMask)
    ends = np.where(endsMask)

    while ends[0][0] < starts[0][0]:
        ends = (ends[0][1:],)

    rowPeaks = []
    for start, end in zip(starts[0], ends[0]):
        if end > start:
            peak_idx = np.argmax(rowSums[start:end]) + start
            rowPeaks.append(peak_idx)

    colsAboveThreshold = colSums > threshold
    startsMask = np.logical_and(~colsAboveThreshold[:-1], colsAboveThreshold[1:])
    starts = np.concatenate(([colsAboveThreshold[0]], startsMask))
    endsMask = np.logical_and(colsAboveThreshold[:-1], ~colsAboveThreshold[1:])
    ends = np.concatenate((endsMask, [colsAboveThreshold[-1]]))
    starts = np.where(startsMask)
    ends = np.where(endsMask)

    while ends[0][0] < starts[0][0]:
        ends = (ends[0][1:],)

    colPeaks = []
    for start, end in zip(starts[0], ends[0]):
        if end > start:
            peak_idx = np.argmax(colSums[start:end]) + start
            colPeaks.append(peak_idx)

    return rowPeaks, colPeaks

def grayscale_strategy(strategy):
    if strategy == "red":
        return [1, 0, 0]
    elif strategy == "green":
        return [0, 1, 0]
    elif strategy == "blue":
        return [0, 0, 1]
    elif strategy == "average":
        return [1/3, 1/3, 1/3]
    elif strategy == "default":
        return [0.299, 0.587, 0.114]
    else:
        raise ValueError("Invalid grayscale strategy")
    
def normalize_image(image):
    min_val = np.min(image)
    max_val = np.max(image)
    if max_val - min_val > 0:
        normalized = (image - min_val) / (max_val - min_val)
    else:
        normalized = image - min_val
    return normalized

def get_colony_location_identifier(orientation_flags, colony_row, colony_col, num_rows, num_cols):
    # 00x - A1 top-left
    # 01x - A1 top-right
    # 10x - A1 bottom-left
    # 11x - A1 bottom-right

    # xx0 - Letters horizontal
    # xx1 - Letters vertical

    if orientation_flags & 0b100:  # Horizontal flip
        colony_col = num_cols - 1 - colony_col
    if orientation_flags & 0b010:  # Vertical flip
        colony_row = num_rows - 1 - colony_row
    if orientation_flags & 0b001:  # Transpose
        colony_row, colony_col = colony_col, colony_row

    letter = chr(ord('A') + colony_row)
    number = colony_col + 1

    return f"{letter}{number}"