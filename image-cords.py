
import cv2

# Initialize global variables
start_point = None
end_point = None
cropping = False

# Mouse callback function
def crop_image(event, x, y, flags, param):
    global start_point, end_point, cropping

    # When the left mouse button is clicked
    if event == cv2.EVENT_LBUTTONDOWN:
        start_point = (x, y)
        cropping = True

    # When the left mouse button is released
    elif event == cv2.EVENT_LBUTTONUP:
        end_point = (x, y)
        cropping = False

        # Draw the rectangle on the original image
        img_copy = param.copy()
        cv2.rectangle(img_copy, start_point, end_point, (0, 255, 0), 2)
        cv2.imshow("Image", img_copy)

        # Calculate top-left and bottom-right points
        x1, y1 = min(start_point[0], end_point[0]), min(start_point[1], end_point[1])
        x2, y2 = max(start_point[0], end_point[0]), max(start_point[1], end_point[1])

        # Print the crop values in a format usable with OpenCV
        print(f"Crop coordinates: Top-left: ({x1}, {y1}), Bottom-right: ({x2}, {y2})")
        print(f"To crop in OpenCV: image[{y1}:{y2}, {x1}:{x2}]")

        # Crop the image and display it
        cropped_img = param[y1:y2, x1:x2]

        if cropped_img.size > 0:
            cv2.imshow("Cropped Image", cropped_img)
        else:
            print("Invalid crop area. Please try again.")

# Load an image (replace 'your_image.jpg' with your image path)
image_path = "training_data/empty.jpg"
image = cv2.imread(image_path)

if image is None:
    print("Error: Could not load the image. Make sure the file path is correct.")
    exit()

# Create a window and set the mouse callback
cv2.namedWindow("Image")
cv2.setMouseCallback("Image", crop_image, image)

# Display the image
while True:
    cv2.imshow("Image", image)
    key = cv2.waitKey(1) & 0xFF
    if key == 27:  # Exit on pressing 'Esc'
        break

# Clean up and close the window
cv2.destroyAllWindows()
