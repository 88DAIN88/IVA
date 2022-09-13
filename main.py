from imageai.Detection.Custom import CustomObjectDetection
import cv2
import time

vid = cv2.VideoCapture("video/video1.mp4")

detector = CustomObjectDetection()
detector.setModelTypeAsYOLOv3()
detector.setModelPath("hololens-ex-60--loss-2.76.h5")
detector.setJsonPath("detection_config.json")
detector.loadModel()

finish = 0

array_detection = []

while (True):
  ret, frame = vid.read()

  start = time.time()
  if start - finish > 1:
    _, array_detection = detector.detectObjectsFromImage(input_image=frame, input_type="array", output_type="array")
    finish = time.time()
    print(array_detection)

  for obj in array_detectiom:
      coord = obj['box_points']
      cv2.rectangle(frame, (coord[0], coord[1]), (coord[2], coord[3]), (0, 0, 255))
      cv2.putText(frame, obj['name'], (coord[0], coord[1] - 6), cv2.FONT_HERSHEY_DUPLEX, 1.0 (255, 255, 255))

  cv2.imshow('TEST ENDO', frame)
  if cv2.waitKey(25) & 0xFF == ord('q'):
    break
camera.close (0)

vid.release()

cv2.destroyAllWindows()
exit(-1)

