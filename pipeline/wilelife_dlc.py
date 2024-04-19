import sys
import logging
from PIL import Image
import numpy as np
import supervision as sv
import torch
import deeplabcut
from PytorchWildlife.models import detection as pw_detection
from PytorchWildlife.models import classification as pw_classification
from PytorchWildlife.data import transforms as pw_trans
from PytorchWildlife import utils as pw_utils


def run_wildlife(input_video):
    DEVICE = "cpu" # Use "cuda" if you are running on GPU. Use "cpu" if you are running on CPU
    SOURCE_VIDEO_PATH = input_video
    TARGET_VIDEO_PATH = input_video[:-4] + "wild.mp4"
    detection_model = pw_detection.MegaDetectorV5(device=DEVICE, pretrained=True)
    classification_model = pw_classification.AI4GAmazonRainforest(device=DEVICE, pretrained=True)
    
    trans_det = pw_trans.MegaDetector_v5_Transform(target_size=detection_model.IMAGE_SIZE,
                                                   stride=detection_model.STRIDE)
    trans_clf = pw_trans.Classification_Inference_Transform(target_size=224)
    
    box_annotator = sv.BoxAnnotator(thickness=4, text_thickness=4, text_scale=2)
    
    def callback(frame: np.ndarray, index: int) -> np.ndarray:
        results_det = detection_model.single_image_detection(trans_det(frame), frame.shape, index)
        labels = []
        for xyxy in results_det["detections"].xyxy:
            cropped_image = sv.crop_image(image=frame, xyxy=xyxy)
            results_clf = classification_model.single_image_classification(trans_clf(Image.fromarray(cropped_image)))
            labels.append("{} {:.2f}".format(results_clf["prediction"], results_clf["confidence"]))
        annotated_frame = box_annotator.annotate(scene=frame, detections=results_det["detections"], labels=labels)
        return annotated_frame
    
    pw_utils.process_video(source_path=SOURCE_VIDEO_PATH, target_path=TARGET_VIDEO_PATH, callback=callback, target_fps=8)
    return TARGET_VIDEO_PATH

def run_deeplabcut(input_video):
    video_path = input_video
    superanimal_name = 'superanimal_quadruped'
    
    # The purpose of the scale list is to aggregate predictions from various image sizes. We anticipate the appearance size of the animal in the images to be approximately 400 pixels.
    scale_list = range(200, 600, 50)
    
    deeplabcut.video_inference_superanimal([video_path], superanimal_name, scale_list=scale_list, video_adapt = False)
    # output: {input_video_filename}DLC_snapshot-700000_labeled.mp4
    
if __name__ == "__main__":
    # Add logging info
    # FORMAT = '%(asctime)s:%(message)s'
    # logging.basicConfig(level=logging.DEBUG, filename='Log.log', filemode='a', format=FORMAT)
    # logging.info(' %s start running...', sys.argv[1])
    
    
    input_video = sys.argv[1]
    wild_result = run_wildlife(input_video)
    run_deeplabcut(wild_result)
    
    # logging.info(' %s is Done.', sys.argv[1])
