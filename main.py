import screen_brightness_control as sbc
import cv2
import mediapipe as mp
from math import hypot
from ctypes import  cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
import numpy as np

# Start capturing video from webcam
wcap, hcap = 640, 480
cap = cv2.VideoCapture(0)
cap.set(3,wcap)
cap.set(4,hcap)
# Initializing the Model
mp_drawing_styles = mp.solutions.drawing_styles
mpHands = mp.solutions.hands
hands = mpHands.Hands()
mpDraw = mp.solutions.drawing_utils
handMesh = mpHands.Hands(
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    max_num_hands=2
)

# Volume Control Library Usage
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume  = cast(interface, POINTER(IAudioEndpointVolume))
volbar=400
volper=0
volMin, volMax = volume.GetVolumeRange()[:2]

while True:
    # Read video frame by frame
    _,image = cap.read()
    # Convert BGR image to RGB image
    imgRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    # Process the RGB image
    results = handMesh.process(imgRGB)
    lmList = []
    # if hands are present in image
    if results.multi_hand_landmarks:
        # detect handmarks
        for handlandmark in results.multi_hand_landmarks:
            for id,lm in enumerate(handlandmark.landmark):
                # store height and width of image
                h, w, c = image.shape
                cx, cy = int(lm.x * w),  int(lm.y * h)
                lmList.append([id, cx, cy])
            # draw Landmarks
            mpDraw.draw_landmarks(image,handlandmark, mpHands.HAND_CONNECTIONS, mp_drawing_styles.get_default_hand_landmarks_style(),
            mp_drawing_styles.get_default_hand_connections_style())

    # If landmarks list is not empty
    if lmList != []:
        # store x,y coordinates of (tip of) thumb
        x1, y1 = lmList[4][1], lmList[4][2]
        # store x,y coordinates of (tip of) index finger
        x2, y2 = lmList[8][1], lmList[8][2]
        # draw circle on thumb and index finger tip
        cv2.circle(image,(x1, y1), 7, (175, 140, 0), cv2.FILLED)
        cv2.circle(image, (x2, y2), 7, (175, 140, 0), cv2.FILLED)

        # draw line from tip of thumb to tip of index finger
        cv2.line(image, (x1, y1), (x2, y2),  (175, 140, 0), 3)
        # calculate square root of the sum
        length = hypot(x2 - x1, y2 - y1)
        #Convert the hand range to the volume range
        vol = np.interp(length, [15, 220], [volMin, volMax])
        volbar = np.interp(length, [30, 300], [400, 150])
        volper = np.interp(length, [30, 300], [0, 100])

        # set brightness
        sbc.set_brightness(int(volper ))

        #Setting the master volume level following the hand range
        volume.SetMasterVolumeLevel(vol, None)

        # Creating volume bar for volume level
        cv2.rectangle(image, (50, 150), (85, 400), (0, 0, 255), 4)
        cv2.rectangle(image, (50, int(volbar)), (85, 400), (0,100, 200), cv2.FILLED)
        cv2.putText(image,f"{int(volper)}%",(10,40),cv2.FONT_ITALIC,1,(0, 255, 98),3)
    cv2.imshow('Image', image)  # Show the video
    if cv2.waitKey(1) & 0xff == ord(' '):  # By using spacebar delay will stop
        break

cap.release()  # stop cam
cv2.destroyAllWindows()
