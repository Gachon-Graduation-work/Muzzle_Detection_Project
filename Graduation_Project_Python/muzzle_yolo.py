import cv2 as cv
import numpy
import numpy as np
import time
from PIL import Image

WHITE = (255, 255, 255)
img = None
img0 = None
outputs = None
startx, starty, width, height = 0, 0, 0, 0
global test_muzzle

# Load names of classes and get random colors
classes = open('obj.names').read().strip().split('\n')
np.random.seed(42)
colors = np.random.randint(0, 255, size=(len(classes), 3), dtype='uint8')

# Give the configuration and weight files for the model and load the network.
net = cv.dnn.readNetFromDarknet('yolov3-tiny.cfg', 'yolov3-custom-tiny.weights')
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
# net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

# determine the output layer
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]


def load_image2(path):
    global img, img0, outputs, ln

    img0 = cv.imread(path, 1)
    img = img0.copy()

    blob = cv.dnn.blobFromImage(img, 1 / 255.0, (416, 416), swapRB=True, crop=False)

    net.setInput(blob)
    t0 = time.time()
    outputs = net.forward(ln)
    t = time.time() - t0

    outputs = np.vstack(outputs)
    post_process(img, outputs, 0.3)

    if test_muzzle:
        img = cv.imread('dog_muzzle.jpg', 1)
        img = numpy.array(img)
        return True, 'None'
    else:
        print("no muzzle")
        from Fierce_dog_classifier import load_image3
        dog_type = load_image3(path)

        if dog_type == 'Fierce Dog':
            return False, 'Fierce Dog'
        else:
            return False, 'Non-Fierce Dog'


def post_process(img, outputs, conf):
    global test_muzzle
    test_muzzle = False
    H, W = img.shape[:2]

    boxes = []
    confidences = []
    classIDs = []

    for output in outputs:
        scores = output[5:]
        classID = np.argmax(scores)
        confidence = scores[classID]

        if confidence > conf:
            x, y, w, h = output[:4] * np.array([W, H, W, H])
            p0 = int(x - w // 2), int(y - h // 2)
            boxes.append([*p0, int(w), int(h)])
            confidences.append(float(confidence))
            classIDs.append(classID)

    indices = cv.dnn.NMSBoxes(boxes, confidences, conf, conf - 0.1)
    if len(indices) > 0:
        test_muzzle = True
        for i in indices.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])
            color = [int(c) for c in colors[classIDs[i]]]
            cv.rectangle(img, (x, y), (x + w, y + h), color, 4)
            text = "{}: {:.4f}".format(classes[classIDs[i]], confidences[i])
            cv.putText(img, text, (x, y - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv.imwrite('dog_muzzle.jpg', img)



# load_image('../pythonProject3/Rottweiler2.jpg')
cv.namedWindow('window')
# cv.createTrackbar('confidence', 'window', 50, 100, trackbar)

cv.destroyAllWindows()