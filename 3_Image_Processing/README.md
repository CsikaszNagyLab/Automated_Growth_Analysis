# Experiment Analysis Workflow Manual

## 1. Setup

To properly manage dependencies, it is recommended to run scripts from a virtual environment. A Python virtual environment can be initialized the following way:

```
python3 -m venv .venv

source .venv/bin/activate  # Under Linux
.venv/Scripts/activate     # Under Windows

pip3 install -r requirements.txt
```

## 2. Calibration with `consoleCalibrator.py`

1. **Start the Calibrator**
   - Run `consoleCalibrator.py` from the command line:
     ```
     python consoleCalibrator.py <folder_with_timelapse_images>
     ```
   - If no folder is provided, you will be prompted to enter the path.

2. **Select a Base Image**
   - Browse through the images and select one where no colonies are visible (i.e., before colony growth starts).
   - Use the on-screen options to navigate and select the image.

3. **Choose Grayscale Conversion**
   - Select the grayscale method that best highlights the plate features (options: default, red, green, blue, average).
   - Preview the result and accept when satisfied.

4. **Adjust Plate Detection Parameters**
   - Modify parameters such as light equalization radius, plate border threshold, and plate distance threshold to ensure at least one blob (plate) is detected for each actual plate.
   - Use the preview to check detection results.

5. **Remove Extra Plates**
   - If extra blobs/plates are detected, remove them using the provided options until only the real plates remain.

6. **Set Plate Borders**
   - Adjust the border location range for each plate as needed.
   - If automatic detection is not accurate, use the manual adjustment option to set plate borders precisely.

7. **Assign Plate Layouts**
   - For each detected plate, assign the correct layout file (CSV) that describes the colony arrangement.
   - You can set layouts for all plates at once or individually.

8. **Select a Colony-Rich Image**
   - Choose an image with many visible colonies for row/column calibration.

9. **Calibrate Colony Grid Detection**
   - Adjust detection parameters so that each row and column of colonies is found.
   - Remove any extra rows or columns that do not correspond to real colonies.
   - Set the correct orientation for letter-number coding (e.g., A1 at top-left, letters horizontal/vertical as needed).

10. **Finish Calibration**
    - When all plates, rows, columns, and orientations are set, export the calibration.
    - A `calibration_results.json` file will be generated in your folder.

---

## 3. Full Analysis with `fullAnalysis.py`

1. **Run the Analysis Script**
   - Execute the following command:
     ```
     python fullAnalysis.py --images=<folder_with_timelapse_images> --data=calibration_results.json --output=output.csv
     ```
   - If you omit any argument, the script will prompt you for the missing information.

2. **Review Output**
   - The script will process all images, extract colony data, and write results to `output.csv`.
   - Each row in the CSV contains: Image, PlateID, ColonyID, ColonyDescriptor, Area, Circularity.

---

## Tips

- Always select a base image with no visible colonies for accurate plate detection.
- Use the preview windows to verify each step before accepting.
- If detection is not perfect, adjust parameters or use manual options.
- The calibration JSON file is essential for the analysis step—do not delete or modify it manually.

---

This workflow ensures accurate calibration and analysis of your cell colony growth experiment.

---

## 4. Quick Start Guide

A short example dataset of 4 images are included in the repository under ./3_Image_Processing/tests/files/experiment. Following through this guide using the dataset will ensure proper installation, as well as provide basic understanding of the intended workflow.

1. Run ```python3 3_Image_Processing/consoleCalibrator.py```
2. As folder path, enter *3_Image_Processing/tests/files/experiment*
3. Ensure that four image files and two layout files have been found, then press 'a' to continue (always make sure that the appearing preview window is active - if it doesn't seem to respond, click on it)
4. The selected base image will appear next. If we assess that it has no colonies visible, press 'a' to confirm.
5. The full image (one with all colonies already visible) appears, confirm this by pressing 'a'
6. In the next phase, different greyscaling terchniques can be assessed. Our dataset is very well differentiated on the red color channel, select this by pressing 'r', then press 'a' to continue.
7. In the next step, we need to ensure, that a single detection seed is present for each plate position. Using default parameters, we will see all 12 plate positions, but Plate 4 has a very small seed. This doesn't obstruct detection of the plate, but we can fix it by slight adjustment of parameters.Press 'b' to change plate border threshold, then in the console prompt, enter 0.14. A new preview will appear, with all seeds similarly sized. Press 'a' to confirm.
8. In the plate enumeration screen we can see all 12 plates recognized, there is no need for manual change - press 'a'.
9. The automatic border detection seems mostly correct, few adjustments need to be made in the following step. Now press 'a'.
10. First, set desired layouts to all plates. Press 'd', then to the console prompt type 1. This sets all plates to layout 1. Then press 'l', and to the prompts input 7, then 2. This sets Plate 7 to layout 2. Repeat this for plates 8-12. <br> We also see, that detection border of some of the plates are well outside plate borders. This can aslo be corrected later, but we can make a few modifications. Press 'p', then select Plate 4. We wan't to adjust its left border, so press 'l', then type in -80 to bring border closer to the middle by 80 pixels. The bottom colonies of Plate 11 are close to the plate border, so we increase it by pressing 'p', select Plate 11, press 'b' for bottom border and type in 20 for increasing by 20 pixels. <br> Press 'a' to continue.
11. Now we can check and adjust colony detection for each plate separately. First thing to notice, that the plate is upside down (A1 and H1 positions should be at the two notches on the right), we can press 'u' to flip numbering to match this. Since A1 and H12 are now recognized as colonies on the opposing sides of the plate, we can continue to Plate 2 by pressing 'a'. <br> Plate 2 has two extra rows: one on the top edge of the image (which is easily recognized by the fact that the first row is numbered 2), and one on the bottom. We can remove these by pressing 'r' (to specify we want to remove an extra row), then type in 1, to remove incorrectly located Row 1. We notice, that rows are numbered again, therefore the extra line on the bottom is no longer No. 10, but No. 9. Remove this by pressing 'r' and typing in 9. A1 and H12 are correctly placed now, press 'a' to continue. <br> Plate 4 has three extra columns at the start, we need to remove them one by one: press c (to remove a column), then select 1. Repeat this two more times (as next extra row will assume position 1). Continue removing all unneccessary lines from each plate.
12. After finishing all individual plates, a final segmentation window is shown.
If we press 'p' and zoom on Plate 1, we can see that H1 and H12 (left-most and right-most colonies of the first row) are not found. To fix this, we need to lower colony detection threshold: press 't' and set threshold to 0.04. This fixes the issue, and all colonies are detected now. <br> A second issue is, that some colonies (like H11 and H12) have one side clipped due to some of them reaching outside the colony ROI. To fix this, press 'r' and set colony ROI radius to 60.
13. When the segmentation preview is satisfactory, we can finalize calibration by pressing 'a'. This generates a calibration_results.json file, containing seed locations for each colony (but not any segmentation result).
14. To conduct segmentation of the experiment, we run ```python3 3_Image_Processing/fullAnalysis.py```. For the images folder, we select *3_Image_Processing/tests/files/experiment*, for colony data file select *3_Image_Processing/tests/files/experiment/calibration_results.json*. The analysis will now run, segment each image and generate an *output.csv* file with all measurements.