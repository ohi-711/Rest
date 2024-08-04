# Partially adapted from https://github.com/ElenaRyumina/EMO-AffectNetModel/blob/main/check_backbone_models_by_webcam.ipynb
# License: MIT

import cv2
import mediapipe as mp
import math
import numpy as np
import os

import torch
from PIL import Image
from torchvision import transforms


class PreprocessInput(torch.nn.Module):
    def __init__(self):
        super(PreprocessInput, self).__init__()

    def forward(self, x):
        x = x.to(torch.float32)
        x = torch.flip(x, dims=(0,))
        x[0, :, :] -= 91.4953
        x[1, :, :] -= 103.8827
        x[2, :, :] -= 131.0912
        return x

class RestDetector:
    def __init__(self, model_path):
        if torch.backends.mps.is_available():
            os.environ['PYTORCH_ENABLE_MPS_FALLBACK'] = '1'
            self.torch_backend = "mps"
        elif torch.cuda.is_available():
            self.torch_backend = "cuda"
        else:
            self.torch_backend = "cpu"

        self.mp_face_mesh = mp.solutions.face_mesh

        self.pth_model = torch.jit.load(model_path).to(self.torch_backend)
        self.pth_model.eval()
        self.DICT_EMO = {0: 'Neutral', 1: 'Joy', 2: 'Sadness', 3: 'Surprise', 4: 'Fear', 5: 'Disgust', 6: 'Anger'}

    def norm_coordinates(self, normalized_x, normalized_y, image_width, image_height):
        x_px = min(math.floor(normalized_x * image_width), image_width - 1)
        y_px = min(math.floor(normalized_y * image_height), image_height - 1)
        return x_px, y_px

    def get_box(self, fl, w, h):
        idx_to_coors = {}
        for idx, landmark in enumerate(fl.landmark):
            landmark_px = self.norm_coordinates(landmark.x, landmark.y, w, h)
            if landmark_px:
                idx_to_coors[idx] = landmark_px

        x_min = np.min(np.asarray(list(idx_to_coors.values()))[:, 0])
        y_min = np.min(np.asarray(list(idx_to_coors.values()))[:, 1])
        endX = np.max(np.asarray(list(idx_to_coors.values()))[:, 0])
        endY = np.max(np.asarray(list(idx_to_coors.values()))[:, 1])

        (startX, startY) = (max(0, x_min), max(0, y_min))
        (endX, endY) = (min(w - 1, endX), min(h - 1, endY))

        return startX, startY, endX, endY

    def pth_processing(self, img):
        ttransform = transforms.Compose([
            transforms.PILToTensor(),
            PreprocessInput()
        ])
        img = img.resize((224, 224), Image.Resampling.NEAREST)
        img = ttransform(img)
        img = torch.unsqueeze(img, 0).to(self.torch_backend)
        return img

    def detect_emotion(self, image_data):
        image_np = np.asarray(bytearray(image_data.read()), dtype=np.uint8)
        image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)

        h, w, _ = image.shape

        with self.mp_face_mesh.FaceMesh(
                max_num_faces=1,
                refine_landmarks=False,
                min_detection_confidence=0.5,
                min_tracking_confidence=0.5) as face_mesh:

            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            results = face_mesh.process(image_rgb)

            if results.multi_face_landmarks:
                for fl in results.multi_face_landmarks:
                    startX, startY, endX, endY = self.get_box(fl, w, h)
                    cur_face = image[startY:endY, startX:endX]

                    cur_face = self.pth_processing(Image.fromarray(cur_face))
                    output = torch.nn.functional.softmax(self.pth_model(cur_face), dim=1).cpu().detach().numpy()

                    cl = np.argmax(output)
                    label = self.DICT_EMO[cl]
                    return label

            return None