import pyrealsense2 as rs
import urx
import cv2
import numpy as np

# camera initialization
def init_cam(fp, pipeline):
	print("-->>sys : initializing Realsense ......")
	for num in range(0, fp):
		_, _, _, _, _, color_image = get_frames_and_images(pipeline)
		test_view = np.copy(color_image)

		hsv = cv2.cvtColor(test_view, cv2.COLOR_RGB2HSV)
		lower_blue = np.array([l_h, l_s, l_v])  #
		upper_blue = np.array([h_h, h_s, h_v])  # FIX
		mask = cv2.inRange(hsv, lower_blue, upper_blue)
		result = cv2.bitwise_and(test_view, color_image, mask=mask)

		ret, thresh = cv2.threshold(result, 127, 255, cv2.THRESH_BINARY)
		blurred0 = cv2.medianBlur(thresh, 5)
		blurred = cv2.cvtColor(blurred0, cv2.COLOR_RGB2GRAY)
		# th3 = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
		_, th3 = cv2.threshold(blurred, 10, 255, cv2.THRESH_BINARY)

		cv2.moveWindow('threshold', 2560 - int(1280 / 2) - 1, 0)
		cv2.imshow('threshold', cv2.resize(th3, (int(1280 / 2), int(720 / 2))))
		cv2.moveWindow('color_image', 2560 - int(1280 / 2) - 1, 390)
		cv2.imshow('color_image', cv2.resize(color_image, (int(1280 / 2), int(720 / 2))))
		cv2.waitKey(2)

# import 한 kinect_snap의 global_cam 클래스를 불러온 오브젝트
# pipeline configuration for streaming
def config_pipeline():
	pipeline = rs.pipeline()
	config = rs.config()
	config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 30)     # problem with resolution: camera not supporting 1280*720
	config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 30)    # problem with resolution: camera not supporting 1280*720
	pipe_profile = pipeline.start(config)
	return pipeline

# returns depth/color frames and images
def get_frames_and_images(pipeline):
	frames = pipeline.wait_for_frames()
	depth_frame = frames.get_depth_frame()
	color_frame = frames.get_color_frame()

	depth_intrin = depth_frame.profile.as_video_stream_profile().intrinsics
	color_intrin = color_frame.profile.as_video_stream_profile().intrinsics
	depth_to_color_extrin = depth_frame.profile.get_extrinsics_to(color_frame.profile)

	depth_image = np.asanyarray(depth_frame.get_data())
	color_image = np.asanyarray(color_frame.get_data())

	return depth_frame, color_frame, depth_image, color_image
