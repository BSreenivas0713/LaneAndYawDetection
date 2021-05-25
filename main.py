import cv2
import numpy as np 
import math
import imgPreprocessing as ip

fileToUse = 6
folderToUse = "labeled/" if fileToUse < 5 else "unlabeled/"

#start video capture
cap = cv2.VideoCapture(folderToUse + str(fileToUse) + ".hevc")

#get training labels if its a training video
lines = []
if fileToUse < 5:
    with open(folderToUse + str(fileToUse) + ".txt") as f:
        lines = [line.rstrip().split() for line in f]

i=0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    h,w = frame.shape[:2]

    thresholded = ip.preprocess(frame)

    birdseye,_,_ = ip.birdseyeView(thresholded)
    
    finalImg = birdseye
    #display training labels for labeled videos
    if fileToUse < 5:
        yawRads = float(lines[i][1])
        cv2.putText(finalImg, 
                    "radians: " + str(round(yawRads,4)), 
                    (50,50), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255,255,255), 2, cv2.LINE_4)
        cv2.putText(finalImg,
                    "degrees: " + str(round(yawRads*180/math.pi, 4)), 
                    (50,80), cv2.FONT_HERSHEY_SIMPLEX, 
                    1, (255,255,255), 2, cv2.LINE_4)

    cv2.imshow('frame', birdseye)
    # cv2.moveWindow('frame', -1300,-600)
    cv2.moveWindow('frame', 100, -100)

    #quit on 'q' press
    if cv2.waitKey(25) & 0xFF == ord('q'):
      break
    i += 1

cap.release()
cv2.destroyAllWindows()