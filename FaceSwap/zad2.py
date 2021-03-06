#!/Users/nic/.virtualenvs/cv/bin

import dlib
import cv2
import numpy as np

import time
import math

import models
import NonLinearLeastSquares
import ImageProcessing

from drawing import *

import FaceRendering
import utils

print "Press T to draw the keypoints and the 3D model"
print "Press R to start recording to a video file"

#you need to download shape_predictor_68_face_landmarks.dat from the link below and unpack it where the solution file is
#http://sourceforge.net/projects/dclib/files/dlib/v18.10/shape_predictor_68_face_landmarks.dat.bz2

#loading the keypoint detection model, the image and the 3D model
predictor_path = "shape_predictor_68_face_landmarks.dat"
image_name = "../data/service.png"
#the smaller this value gets the faster the detection will work
#if it is too small, the user's face might not be detected
maxImageSizeForDetection = 320

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(predictor_path)
mean3DShape, blendshapes, mesh, idxs3D, idxs2D = utils.load3DFaceModel("../candide.npz")

projectionModel = models.OrthographicProjectionBlendshapes(blendshapes.shape[0])

modelParams = None
lockedTranslation = False
drawOverlay = False
cap = cv2.VideoCapture(0)
writer = None
cameraImg = cap.read()[1]
together = None

fourcc = cv2.VideoWriter_fourcc(*'x264')
#fourcc = 0x00000021

textureImg = cv2.imread(image_name)
textureCoords = utils.getFaceTextureCoords(textureImg, mean3DShape, blendshapes, idxs2D, idxs3D, detector, predictor)
renderer = FaceRendering.FaceRenderer(cameraImg, textureImg, textureCoords, mesh)

texShapes2D = utils.getFaceKeypoints(textureImg, detector, predictor, maxImageSizeForDetection)
shapes2D = None

while True:
    
    if shapes2D is not None and texShapes2D is not None:
        for idx, shape2D in enumerate(shapes2D):
            #3D model parameter initialization
            modelParams = projectionModel.getInitialParameters(mean3DShape[:, idxs3D], shape2D[:, idxs2D])

            #3D model parameter optimization
            modelParams = NonLinearLeastSquares.GaussNewton(modelParams, projectionModel.residual, projectionModel.jacobian, ([mean3DShape[:, idxs3D], blendshapes[:, :, idxs3D]], shape2D[:, idxs2D]), verbose=0)

            texModelParams = projectionModel.getInitialParameters(mean3DShape[:, idxs3D], texShapes2D[idx][:, idxs2D])
            texModelParams = NonLinearLeastSquares.GaussNewton(modelParams, projectionModel.residual, projectionModel.jacobian, ([mean3DShape[:, idxs3D], blendshapes[:, :, idxs3D]], texShapes2D[idx][:, idxs2D]), verbose=0)


            #rendering the model to an image
            textureCoords = utils.getFaceTextureCoords(cameraImg, mean3DShape, blendshapes, idxs2D, idxs3D, detector, predictor)
            renderer.set_faceTexture(cameraImg, textureCoords)
            t = (1+math.sin(2*math.pi*time.time()/10))/2
            shape3D = utils.getShape3D(mean3DShape, blendshapes, modelParams, texModelParams, t)
            renderedImg = renderer.render(shape3D)

            #blending of the rendered face with the image
            mask = np.copy(renderedImg[:, :, 0])
            renderedImg = ImageProcessing.colorTransfer(cameraImg, renderedImg, mask)
            webcamImg = ImageProcessing.blendImages(renderedImg, cameraImg, mask)
       

            #drawing of the mesh and keypoints
            if drawOverlay:
                drawPoints(cameraImg, shape2D.T)
                drawProjectedShape(cameraImg, [mean3DShape, blendshapes], projectionModel, mesh, modelParams, lockedTranslation)
                drawPoints(renderedImg, texShapes2D[idx].T)
                drawProjectedShape(renderedImg, [mean3DShape, blendshapes], projectionModel, mesh, texModelParams, lockedTranslation)

            """height, width, channels = cameraImg.shape
            cameraImg = cameraImg[0:height , (width-height)/2:(width+height)/2, :]
            webcamImg = webcamImg[0:height , (width-height)/2:(width+height)/2, :]
            together = np.concatenate((cameraImg, webcamImg), axis=1)
            """
    else:
        cameraImg = cap.read()[1]
        webcamImg = np.copy(cameraImg)

        height, width, channels = cameraImg.shape
        cameraImg = cameraImg[0:height , (width-height)/2:(width+height)/2, :]
        webcamImg = webcamImg[0:height , (width-height)/2:(width+height)/2, :]

    if writer is not None:
        writer.write(webcamImg)

    cv2.imshow('image', webcamImg)
    key = cv2.waitKey(1)

    if key == ord('c') and shapes2D is None:
        cameraImg = cap.read()[1]
        webcamImg = np.copy(cameraImg)
        height, width, channels = cameraImg.shape
        cameraImg = cameraImg[0:height , (width-height)/2:(width+height)/2, :]
        webcamImg = webcamImg[0:height , (width-height)/2:(width+height)/2, :]
        shapes2D = utils.getFaceKeypoints(cameraImg, detector, predictor, maxImageSizeForDetection)
        #print shapes2D
        #print texShapes2D

    if key == 27:
        break
    if key == ord('t'):
        drawOverlay = not drawOverlay
    if key == ord('r'):
        if writer is None:
            print "Starting video writer"
            writer = cv2.VideoWriter("../out.mp4", fourcc, 25, (webcamImg.shape[1], webcamImg.shape[0]))

            if writer.isOpened():
                print "Writer succesfully opened"
            else:
                writer = None
                print "Writer opening failed"
        else:
            print "Stopping video writer"
            writer.release()
            writer = None