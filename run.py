import cv2 
import os
import numpy as np
import tensorflow as tf
import pyautogui
import time
from object_detection.utils import config_util
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
from object_detection.builders import model_builder

ANNOTATION_PATH = './annotations'
MODEL_PATH = './models'
CONFIG_PATH = MODEL_PATH+'/my_ssd_mobnet/pipeline.config'
CHECKPOINT_PATH = MODEL_PATH+'/my_ssd_mobnet/'

configs = config_util.get_configs_from_pipeline_file(CONFIG_PATH)
detection_model = model_builder.build(model_config=configs['model'], is_training=False)

@tf.function
def detect_fn(image):
    image, shapes = detection_model.preprocess(image)
    prediction_dict = detection_model.predict(image, shapes)
    detections = detection_model.postprocess(prediction_dict, shapes)
    return detections


if __name__ == "__main__":
    
    category_index = label_map_util.create_category_index_from_labelmap(ANNOTATION_PATH+'/label_map.pbtxt')
    
    # Restore checkpoint
    ckpt = tf.compat.v2.train.Checkpoint(model=detection_model)
    ckpt.restore(os.path.join(CHECKPOINT_PATH, 'ckpt-11')).expect_partial()

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    # Queue - to be sure about your gesture script has to collect 'q_threshold' amount of frames with high enough confidence and same gesture
    q = []
    q_threshold = 20
    while True: 
        ret, frame = cap.read()
        image_np = np.array(frame)
        
        input_tensor = tf.convert_to_tensor(np.expand_dims(image_np, 0), dtype=tf.float32)
        detections = detect_fn(input_tensor)
        
        num_detections = int(detections.pop('num_detections'))
        detections = {key: value[0, :num_detections].numpy()
                    for key, value in detections.items()}
        detections['num_detections'] = num_detections
        # detection_classes should be ints.
        detections['detection_classes'] = detections['detection_classes'].astype(np.int64)
        if(detections['detection_scores'][0] > 0.6):
            q.append(detections['detection_classes'][0])
            if(len(q)>q_threshold):
                q.pop(0)
            if(all(x==q[0] for x in q) and len(q) == q_threshold):
                if(detections['detection_classes'][0]==0):
                    pyautogui.press("k")
                elif(detections['detection_classes'][0]==1):
                    pyautogui.press("j")
                elif(detections['detection_classes'][0]==2):
                    pyautogui.press("l")
                    time.sleep(0.3)
                    pyautogui.press("enter")
                elif(detections['detection_classes'][0]==3):
                    pyautogui.press("l")
                    time.sleep(0.3)
                    pyautogui.press("right")
                    time.sleep(0.3)
                    pyautogui.press("enter")
                q.clear()
        else:
            q.clear()
                
        label_id_offset = 1
        image_np_with_detections = image_np.copy()

        viz_utils.visualize_boxes_and_labels_on_image_array(
                    image_np_with_detections,
                    detections['detection_boxes'],
                    detections['detection_classes']+label_id_offset,
                    detections['detection_scores'],
                    category_index,
                    use_normalized_coordinates=True,
                    max_boxes_to_draw=1,
                    min_score_thresh=.65,
                    agnostic_mode=False)

        cv2.imshow('object detection',  cv2.resize(image_np_with_detections, (800, 500)))
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            cap.release()
            break