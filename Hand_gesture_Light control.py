import cv2 as cv
import mediapipe as mp
import numpy as np
from websocket import create_connection


cap = cv.VideoCapture(0)
mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils



ws = create_connection("ws://192.168.43.183:81")
hand = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.5, min_tracking_confidence=0.5)

def send_payload(msg):
    ws.send(msg)


def detect_hands(img, hands):
    img_c = img.copy()
    img = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
    img.flags.writeable=False

    results = hands.process(img)
    img.flags.writeable=True
    img = cv.cvtColor(img, cv.COLOR_RGB2BGR)
    
    if results.multi_hand_landmarks:
        for hand_landmark in results.multi_hand_landmarks:
            mp_draw.draw_landmarks(img_c, hand_landmark, mp_hands.HAND_CONNECTIONS)

    return img_c, results




def count_f(image, results):
    height, width, _ = image.shape
    img_ = image.copy()
    count = {'Right': 0, 'Left' : 0}
    finger_tip_ids = [mp_hands.HandLandmark.RING_FINGER_TIP, mp_hands.HandLandmark.PINKY_TIP, 
    mp_hands.HandLandmark.INDEX_FINGER_TIP, mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

    finger_status = {'right_thumb': False, 'right_index': False, 'right_middle': False, 
    'right_ring': False, 'right_pinky': False, 'left_thumb': False, 'left_index': False, 
    'left_middle': False, 'left_ring': False, 'left_pinky': False}


    for hand_index, hand_info in enumerate(results.multi_handedness):
        hand_label = hand_info.classification[0].label
        hand_landmarks = results.multi_hand_landmarks[hand_index] 

        for tip_ind in finger_tip_ids:
            finger = tip_ind.name.split("_")[0]

            if hand_landmarks.landmark[tip_ind].y < hand_landmarks.landmark[tip_ind - 2].y:
                finger_status[hand_label+"_"+finger] = True
                count[hand_label]+=1

    thumb_tip_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP].x

    thumb_mcp_x = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP - 2].x

    if hand_label == 'Right' and thumb_tip_x < thumb_mcp_x or hand_label == 'Left' and thumb_tip_x > thumb_mcp_x:
        finger_status[hand_label+"_thumb"] = True
        count[hand_label]+=1

    # cv.putText(img_, "Total Fingers:", (10, 25), cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)
    # cv.putText(img_, str(sum(count.values())), (width//2-150, 240), cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)

    return img_, finger_status, count
            







while cap.isOpened():
    ret, frame = cap.read()
    # feed_model = pre_process(frame)
    
    frame = cv.flip(frame, 1)

    frame, results = detect_hands(frame, hand)

    if results.multi_hand_landmarks:
        frame, finger_stat, count = count_f(frame, results)
        count_finger = sum(count.values())
        if count_finger == 0:
            send_payload("Off")
            cv.putText(frame, "Light_State: OFF", (10, 25), cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)
        elif count_finger == 5:
            send_payload("On")
            cv.putText(frame, "Light_State: ON", (10, 25), cv.FONT_HERSHEY_COMPLEX, 1, (0, 255, 0), 1)
    
    cv.imshow("feed", frame)

    if cv.waitKey(1)&0xFF == ord('x'):
        break
cap.release()
