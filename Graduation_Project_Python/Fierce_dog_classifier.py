from __future__ import print_function, division

import torch
import cv2 as cv
from torchvision import transforms
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
from pathlib import Path


def load_image3(path):
    img = Image.open(path)
    class_names = ['Fierce Dog', 'Non Fierce Dog']

    model = torch.load('model20211207.pt')

    trans = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    input = trans(img)
    input = input.view(1, 3, 224, 224)

    # Generate prediction
    prediction = model(input.cuda())

    # Predicted class value using argmax
    predicted_class = prediction.argmax()

    return class_names[predicted_class]