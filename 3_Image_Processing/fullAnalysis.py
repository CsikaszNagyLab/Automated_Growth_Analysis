import sys
import os
import analyzePlate
import cvHelper

images_folder = ""
colony_data_file = ""
output_file = ""

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        if arg.startswith("--images="):
            images_folder = arg[len("--images="):]
        elif arg.startswith("--data="):
            colony_data_file = arg[len("--data="):]
        elif arg.startswith("--output="):
            output_file = arg[len("--output="):]

    print("\nExperiment Analysis Tool\n")
    while not images_folder:
        images_folder = input("Enter the path to the images folder: ").strip()
    while not colony_data_file:
        colony_data_file = input("Enter the path to the colony data file: ").strip()

    if not output_file:
        output_file = "output.csv"
        print(f"No output file specified. Using default: {output_file}")

    configuration = analyzePlate.read_configuration(colony_data_file)

    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif'}
    images = []
    for filename in os.listdir(images_folder):
        if os.path.isfile(os.path.join(images_folder, filename)):
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_extensions:
                images.append(os.path.join(images_folder, filename))

    if not images:
        print(f"No images found in folder: {images_folder}")
        sys.exit(1)
    
    with open(output_file, 'w') as out_file:
        out_file.write("Image,PlateID,ColonyID,ColonyDescriptor,Area,Circularity,CenterDistance\n")
        i = 0
        for image_path in images:
            i += 1
            print(f"Processing image: {image_path}")
            results = analyzePlate.analyze_single_image(image_path, configuration)
            for result in results:
                out_file.write(f"{result.image_name},{result.plate_id},{result.colony_id},{result.colony_descriptor},{result.area},{result.circularity},{result.centerDistance}\n")

            print(f"Image {i}/{len(images)} processed.")