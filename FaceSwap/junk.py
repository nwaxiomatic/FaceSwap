renderer.set_faceTexture(cameraImg, textureCoords)
            shape3D = utils.getShape3D(mean3DShape, blendshapes, modelParams, texModelParams)
            renderedImg = renderer.render(shape3D)

            #blending of the rendered face with the image
            mask = np.copy(renderedImg[:, :, 0])
            renderedImg = ImageProcessing.colorTransfer(cameraImg, renderedImg, mask)
            cameraImg = ImageProcessing.blendImages(renderedImg, cameraImg, mask)

  export DYLD_LIBRARY_PATH=/Users/nic/anaconda/pkgs/mkl-2017.0.1-0/lib