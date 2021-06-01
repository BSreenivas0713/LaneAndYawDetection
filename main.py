import cv2
import numpy as np 
import math
import imgPreprocessing as ip
import featureProcessing
import sys
import detectLanes as dl
import time
from collections import deque

leftLaneLine = dl.Line()
rightLaneLine = dl.Line()

def findMatchingDirection(avgMatchingDirection):
    sumX = 0
    sumY = 0
    for x, y in avgMatchingDirection:
        sumX += x
        sumY += y
    return sumX/len(avgMatchingDirection), sumY/len(avgMatchingDirection)

def projectLineOntoRoad(srcImg, leftLaneLine, rightLaneLine, Minv):
    height, width = srcImg.shape[:2]

    leftCoefs = leftLaneLine.avgCoefs()
    rightCoefs = rightLaneLine.avgCoefs()

    yLinspace = np.linspace(0, height - 1, height)
    left_fitx = leftCoefs[0] * yLinspace ** 2 + leftCoefs[1] * yLinspace + leftCoefs[2]
    right_fitx = rightCoefs[0] * yLinspace ** 2 + rightCoefs[1] * yLinspace + rightCoefs[2]

    road_warp = np.zeros_like(srcImg, dtype=np.uint8)
    pts_left = np.array([np.transpose(np.vstack([left_fitx, yLinspace]))])
    pts_right = np.array([np.flipud(np.transpose(np.vstack([right_fitx, yLinspace])))])
    pts = np.hstack((pts_left, pts_right))
    cv2.fillPoly(road_warp, np.int_([pts]), (0, 255, 0))
    road_dewarped = cv2.warpPerspective(road_warp, Minv, (width, height))

    blend_onto_road = cv2.addWeighted(srcImg, 1., road_dewarped, 0.3, 0)

    imgWithLines = np.zeros_like(srcImg)
    imgWithLines = leftLaneLine.draw(imgWithLines, color=(255, 0, 0))
    imgWithLines = rightLaneLine.draw(imgWithLines, color=(0, 0, 255))
    linesDewarped = cv2.warpPerspective(imgWithLines, Minv, (width, height))

    lines_mask = srcImg.copy()
    idx = np.any([linesDewarped != 0][0], axis=2)
    lines_mask[idx] = linesDewarped[idx]

    blend_onto_road = cv2.addWeighted(src1=lines_mask, alpha=0.8, src2=blend_onto_road, beta=0.5, gamma=0.)

    return blend_onto_road


def main(fileToUse, folderToUse):
    global leftLaneLine, rightLaneLine
    #start video capture
    cap = cv2.VideoCapture(folderToUse + str(fileToUse) + ".hevc")

    #get training labels if its a training video
    lines = []
    if fileToUse < 5:
        with open(folderToUse + str(fileToUse) + ".txt") as f:
            lines = [line.rstrip().split() for line in f]
    
    fp = featureProcessing.FeatureProcessing()

    avgMatchingDirection = deque(maxlen=50)

    i=0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        h,w = frame.shape[:2]

        thresholded = ip.preprocess(frame)

        birdseye,_,Minv = ip.birdseyeView(thresholded)

        # lanesDetected, leftLaneLine, rightLaneLine = dl.slidingWindowSearch(birdseye, leftLaneLine, rightLaneLine)
        
        # linesDewarped = projectLineOntoRoad(frame, leftLaneLine, rightLaneLine, Minv)

        matches = fp.getFeatures(birdseye)
        finalImg = frame

        totalV = None
        numTimes = 0
        for p1, p2 in matches:
            u1,v1 = map(lambda x: int(round(x)), p1.pt)
            u2,v2 = map(lambda x: int(round(x)), p2.pt)
            vector = np.array([u2-u1,v2-v1])
            mag = np.linalg.norm(vector)
            if mag > 50:
                continue
            vHat = vector/np.linalg.norm(vector)
            # print(vHat)
            if not np.isnan(vHat[0]) and not np.isnan(vHat[1]):
                if totalV is None:
                    totalV = vHat
                    # print(totalV)
                else:
                    totalV += vHat
                numTimes += 1
            # cv2.circle(finalImg, (u1,v1), color=(0,255,0), radius=3)
            # cv2.line(finalImg, (u1,v1), (u2,v2), color=(255,0,0))
        # print(totalV)
        if totalV is not None:
            currAvgX, currAvgY = totalV / numTimes
            avgMatchingDirection.append((currAvgX,currAvgY))
            avgX, avgY = findMatchingDirection(avgMatchingDirection)
            cv2.putText(finalImg, 
                            "avgX: " + str(1000*round(avgX,4)), 
                            (50,110), cv2.FONT_HERSHEY_SIMPLEX, 
                            1, (255,255,255), 2, cv2.LINE_4)
            cv2.putText(finalImg, 
                            "avgY: " + str(1000*round(avgY,4)), 
                            (50,140), cv2.FONT_HERSHEY_SIMPLEX, 
                            1, (255,255,255), 2, cv2.LINE_4)
            xBase = 500
            yBase = 500
            cv2.arrowedLine(finalImg, (xBase,yBase), (int(xBase+1000*avgX),int(yBase+1000*avgY)), color=(255,0,0), thickness=5)
        
        # print(leftLaneLine.xCoords)
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

        cv2.imshow('frame', finalImg)
        # cv2.moveWindow('frame', -1300,-600)
        cv2.moveWindow('frame', 100, -100)

        #quit on 'q' press
        if cv2.waitKey(25) & 0xFF == ord('q'):
            break
        i += 1
        

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    #command line input for which file to use
    fileToUse = int(sys.argv[1])
    folderToUse = "labeled/" if fileToUse < 5 else "unlabeled/"
    main(fileToUse, folderToUse)