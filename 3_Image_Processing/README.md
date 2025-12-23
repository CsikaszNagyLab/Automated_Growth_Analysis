# Experiment Analysis Workflow Manual

## 1. Calibration with `consoleCalibrator.py`

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

## 2. Full Analysis with `fullAnalysis.py`

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
