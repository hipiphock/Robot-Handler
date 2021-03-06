import time
import os
import copy

import cv2
import urx
import numpy as np
from Calibration.Helper import nothing, create_directory
import Calibration.CameraStream as CameraStream
import Calibration.RobotHandler as RobotHandler

def get_max_radius(contours):
    max_radius = 0
    cx, cy = None, None
    for cnt in contours:
        if cv2.contourArea(cnt) < 60000:
            (cx, cy), radius = cv2.minEnclosingCircle(cnt)
            if radius > max_radius:
                max_radius = radius
    return max_radius, cx, cy

def save_image(image, save_dir):
    time_str = time.strftime('%Y%m%d-%H-%M-%S', time.localtime(time.time()))
    file_name = time_str + ".png"
    file_path = os.path.join(save_dir, file_name)
    cv2.imwrite(file_path, image)
    print("-->>sys :  img_saved ")

# save filter and exit program
def save_filter_and_exit(save_dir, low_h, low_s, low_v, high_h, high_s, high_v):
    print("-->>sys :  Exit program ")
    file_name = "hsv_result.txt".format(save_dir)
    file_path = os.path.join(save_dir, file_name)
    f = open(file_path, "a")
    f.write("{}".format(save_dir, time.strftime('%Y%m%d-%H-%M-%S', time.localtime(time.time()))))
    f.write("\n-->>sys :  low__Result ~ H:{0:3d}, S:{1:3d}, V:{2:3d}".format(low_h, low_s, low_v))
    f.write("\n-->>sys :  high_Result ~ H:{0:3d}, S:{1:3d}, V:{2:3d}".format(high_h, high_s, high_v))
    f.close()

# TODO: should change it to appropriate form
def read_hsv_filter(hsv_filter_path):
    f_hsv = open(hsv_filter_path, "r")
    line = []
    i = 0
    while True:
        text = f_hsv.readline()
        data_line = text.strip('\n')
        if text.__len__() == 0:
            break
        else:
            line.append(data_line)
            print("contents : " + data_line)
            i += 1

    l_h = int(line[-2][-17:-14])
    l_s = int(line[-2][-10:-7])
    l_v = int(line[-2][-3:])
    low_hsv = [l_h, l_s, l_v]

    h_h = int(line[-1][-17:-14])
    h_s = int(line[-1][-10:-7])
    h_v = int(line[-1][-3:])
    high_hsv = [h_h, h_s, h_v]
    return low_hsv, high_hsv

# get image and convert color image into numpy array
def save_hsv_filter(pipeline, cam_robot, nocam_robot, save_dir):
    """
    generates and saves hsv filter.
    the hsv filter will be used later
    """
    cv2.namedWindow('result')
    cv2.namedWindow('th3')
    cv2.namedWindow('bar')
    cv2.resizeWindow('bar', 640, 320)

    # opencv 함수 트랙바 생성 (트랙바의 이름, 띄울 창, 0~n, 변화시)
    # 수작업을 통해서 trackbar에서 가장 appropriate한 hsv를 골라야 한다.
    cv2.createTrackbar('low_h', 'bar', 0, 180, nothing)
    cv2.createTrackbar('low_s', 'bar', 0, 255, nothing)
    cv2.createTrackbar('low_v', 'bar', 0, 255, nothing)

    cv2.createTrackbar('high_h', 'bar', 0, 180, nothing)
    cv2.createTrackbar('high_s', 'bar', 0, 255, nothing)
    cv2.createTrackbar('high_v', 'bar', 0, 255, nothing)
    cv2.setTrackbarPos('high_h', 'bar', 180)
    cv2.setTrackbarPos('high_s', 'bar', 255)
    cv2.setTrackbarPos('high_v', 'bar', 255)

    create_directory(save_dir)

    put_it_on_flag = 0

    while True:  # : 프로그램이 돌아가는 영역 - 반복      
        _, _, _, color_image = CameraStream.get_frames_and_images(pipeline)

        img = color_image
        # img = cv2.resize(img, (int(1280 / 2), int(720 / 2)))  # : 이미지 변형
        hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)  # : 이미지를 RGB에서 HSV로 변환후 저장

        # get info from track bar and apply to result    # : 트랙바의 현재 상태를 받아 저장 (해당 트랙바 이름, 뜨운 창)
        low_h = cv2.getTrackbarPos('low_h', 'bar')
        low_s = cv2.getTrackbarPos('low_s', 'bar')
        low_v = cv2.getTrackbarPos('low_v', 'bar')

        high_h = cv2.getTrackbarPos('high_h', 'bar')
        high_s = cv2.getTrackbarPos('high_s', 'bar')
        high_v = cv2.getTrackbarPos('high_v', 'bar')

        # Normal masking algorithm
        lower_color = np.array([low_h, low_s, low_v])  # : 각  h,s,v를 저장하는 배열생성
        upper_color = np.array([high_h, high_s, high_v])  # : 각 최대 값

        # : 스레스홀드를 lower_color로 지정하여, 이하는 0값을 출력, 범위안의 것은 255를 출력하여 마스크를 생성
        mask = cv2.inRange(hsv, lower_color, upper_color)

        # : 마스크를 씌운 이미지와 마스크를 씌우지 않은 이미지에서 모두 0이 아닌경우에만 출력
        result = cv2.bitwise_and(img, img, mask=mask)

        ret, thresh = cv2.threshold(result, 16, 255, cv2.THRESH_BINARY)  # : 스레스홀드 127로 설정, 최대 255
        blurred = cv2.medianBlur(thresh, 5)  # : 메디안 필터를 이용한 블러
        blurred = cv2.cvtColor(blurred, cv2.COLOR_RGB2GRAY)  # : 그레이스케일로 변환
        # th3 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11,
        #                             2)  # : 가우시안, 어뎁티브 스레스홀드
        _, th3 = cv2.threshold(blurred, 10, 255, cv2.THRESH_BINARY)

        contours, hierarchy = cv2.findContours(th3, mode=cv2.RETR_EXTERNAL,
                                               method=cv2.CHAIN_APPROX_SIMPLE)  # : opencv 4
        cv2.drawContours(result, contours, -1, (0, 255, 0), 2)

        # get maximum radius of enclosing circle
        max_radius, cx, cy = get_max_radius(contours)

        fontScale = 1
        color = (0, 0, 255)  # : BGR
        location = (0, 50)
        font = cv2.FONT_ITALIC
        try:
            cx, cy = int(cx), int(cy)
            if 0 < max_radius <= 3:
                print("-->>hsv : put it closer!")
                cv2.rectangle(result, (0, 0), 1280, 720, (0, 0, 255), 2)  # draw circle in red color
            elif max_radius is 0:
                text = "-->>hsv : NoBall yeah. put it ON!"
                cv2.putText(result, text, location, font, fontScale, color)
                cv2.rectangle(result, (0, 0), 1280, 720, (0, 0, 255), 2)  # draw circle in red color
            else:
                cv2.circle(result, (int(cx), int(cy)), int(max_radius), (0, 0, 255), 2)  # draw circle in red color
                put_it_on_flag = 0
        except:
            put_it_on_flag += 1
            if 1 <= put_it_on_flag:
                if put_it_on_flag == 1:
                    print("-->>hsv : Can't Find the ball")
            else:
                pass
            text = "-->>hsv : Can't Find the ball"
            thickness = 1
            color = (0, 0, 255)  # : BGR
            location = (0, 100)
            font = cv2.FONT_ITALIC
            cv2.rectangle(result, (0, 0), (1280, 720), (0, 0, 255), 2)  # draw circle in red color
            cv2.putText(result, text, location, font, thickness, color)

        cv2.moveWindow('bar', 1920 - int(1280 / 2) - 1, 0)
        cv2.moveWindow('result', 1920 - int(1280 / 2) - 1, 320)
        cv2.moveWindow('th3', 1920 - int(1280 / 2) - 1, 680)

        img_ = copy.deepcopy(img)
        th_list = np.argwhere(th3 == 255)
        img_[th_list[:, 0], th_list[:, 1], :] = 255
        result_ = cv2.resize(result, (int(1280 / 2), int(720 / 2)))
        img_ = cv2.resize(img_, (int(1280 / 2), int(720 / 2)))

        cv2.imshow('result', result_)
        cv2.imshow('th3', img_)

        k = cv2.waitKey(1)
        if k == ord('s'):
            print("-->>sys :  low__Result : H : {}, S : {}, V : {}".format(low_h, low_s, low_v))
            print("-->>sys :  high_Result : H : {}, S : {}, V : {}".format(high_h, high_s, high_v))
            save_image(img, save_dir)
        if k == ord('h'):
            center = np.deg2rad([-35.45, -62.40, 117.18, -0.87, 67.47, -207.88])
            rob2.movej(center, 1, 1)
        if k == ord('['):
            left_front = [-0.7646004409924503, -0.2769095597792518, -0.09287284815199578,
                        -2.6180463593646133, 0.00021286950964079492, 9.026852509835078e-05]
            rob2.movel(left_front, 1, 1)
        if k == ord(';'):
            left_back = [-0.29020377434533084, -0.2769095596279693, -0.09287284816344174,
                        -2.6180463593017174, 0.00021286953063727208, 9.026852449625093e-05]
            rob2.movel(left_back, 1, 1)
        if k == ord(']'):
            right_front = [-0.75860210749507, 0.3132149404349904, -0.09287284813507735,
                        -2.618046359176607, 0.00021286949160195535, 9.026851967238821e-05]
            rob2.movel(right_front, 1, 1)
        if k == ord('\''):
            right_back = [-0.288681430161438, 0.31321494043497256, -0.09287284813508721,
                        -2.6180463591763017, 0.00021286949158524576, 9.026852011591973e-05]
            rob2.movel(right_back, 1, 1)

        if k & 0xFF == 27:  # ESC
            save_filter_and_exit(save_dir, low_h, low_s, low_v, high_h, high_s, high_v)
            cv2.destroyAllWindows()
            break