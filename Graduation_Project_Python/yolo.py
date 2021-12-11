import cv2 as cv
import numpy as np
import time
from PIL import Image

WHITE = (255, 255, 255)
img = None
img0 = None
outputs = None
global danger

# Load names of classes and get random colors
classes = open('coco.names').read().strip().split('\n')
np.random.seed(42)
colors = np.random.randint(0, 255, size=(len(classes), 3), dtype='uint8')

# Give the configuration and weight files for the model and load the network.
net = cv.dnn.readNetFromDarknet('yolov3.cfg', 'yolov3.weights')
net.setPreferableBackend(cv.dnn.DNN_BACKEND_OPENCV)
# net.setPreferableTarget(cv.dnn.DNN_TARGET_CPU)

# determine the output layer
ln = net.getLayerNames()
ln = [ln[i[0] - 1] for i in net.getUnconnectedOutLayers()]


def load_image(path):
    global img, img0, outputs, ln, danger

    img0 = cv.imread(path, 1)
    img = img0.copy()

    blob = cv.dnn.blobFromImage(img, 1 / 255.0, (416, 416), swapRB=True, crop=False)

    net.setInput(blob)
    outputs = net.forward(ln)

    outputs = np.vstack(outputs)
    post_process(img, outputs, 0.5)
    return danger


def post_process(img, outputs, conf):
    global startx, starty, width, height, danger
    danger = False
    H, W = img.shape[:2]

    boxes = []
    confidences = []
    classIDs = []

    for output in outputs:
        scores = output[5:]
        classID = np.argmax(scores)
        confidence = scores[classID]

        # classID = 16 즉 개인 경우 & 개일 확률이 threshold(0.5)보다 큰 경우
        if confidence > conf and classID == 16:
            x, y, w, h = output[:4] * np.array([W, H, W, H])
            p0 = int(x - w // 2), int(y - h // 2)
            boxes.append([*p0, int(w), int(h)])
            confidences.append(float(confidence))
            classIDs.append(classID)

    # 최종적으로 살아남은 박스 들
    indices = cv.dnn.NMSBoxes(boxes, confidences, conf, conf - 0.1)
    if len(indices) > 0:
        j = 1
        # 각 이미지마다 확인
        for i in indices.flatten():
            (x, y) = (boxes[i][0], boxes[i][1])
            (w, h) = (boxes[i][2], boxes[i][3])

            color = [int(c) for c in colors[classIDs[i]]]
            # 현재 img = picture.jpg (전체사진)
            cv.rectangle(img, (x, y), (x + w, y + h), color, 2)
            # 뒤의 img[]부분은 개가 발견될 경우 CROP 할 범위를 나타냄, 개 crop된 사진 저장
            cv.imwrite('dog'+str(j)+'.jpg', img[y: y+h, x:x+w])

            # crop된 사진을 각각 muzzle_yolo로 보냄
            from muzzle_yolo import load_image2
            # return되는 값은 1. muzzle의 유무(있으면 true 없으면 false)
            # 2. 개가 맹견인지 여부 (muzzle이 있을 경우 None이 넘어옴)
            result_muzzle_bool, result_dog_type = load_image2('dog'+str(j)+'.jpg')

            # muzzle이 있는 경우 -> muzzle이 박스쳐진 사진으로 덮어줌
            # text는 muzzle 있음
            if result_muzzle_bool is True:
                text = 'This dog has muzzle!'
                img = Image.open('picture.jpg')
                img_size = img.size
                img_to_paste = Image.open('dog_muzzle.jpg')
                new_image = Image.new('RGB', (img_size[0], img_size[1]), (250, 250, 250))
                new_image.paste(img, (0, 0))
                new_image.paste(img_to_paste, (x, y))
                # 기존의 picture.jpg 즉 전체사진에 crop된 사진을올린 새로운 사진을 picture.jpg로 대체
                new_image.save("picture.jpg", "JPEG")
                img = cv.imread('picture.jpg', 1)
                cv.putText(img, text, (x, y - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv.imwrite('picture.jpg', img)

            # muzzle이 없는 경우 -> muzzle 박스 없음
            # text는 muzzle 없음, 맹견 인지 아닌지
            else:
                text = 'No muzzle!' + ' This dog is ' + str(result_dog_type)
                if result_dog_type == 'Fierce Dog':
                    danger = True
                cv.putText(img, text, (x, y - 5), cv.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
                cv.imwrite('picture.jpg', img)

            j = j+1

        img = cv.resize(img, (800, 800), interpolation=cv.INTER_AREA)
        cv.imshow('window', img)
        cv.waitKey(0)

    cv.imwrite('picture.jpg', img)


cv.namedWindow('window')
cv.destroyAllWindows()