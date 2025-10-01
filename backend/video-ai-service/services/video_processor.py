import os
import cv2
import subprocess
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VideoProcessor:
    def __init__(self, annotated_folder=None):
        # Folder to save annotated video (can be anywhere)
        env_annotated = os.getenv("ANNOTATED_FOLDER", "/tmp/annotated_videos")
        self.annotated_folder = os.path.abspath(annotated_folder or env_annotated)
        os.makedirs(self.annotated_folder, exist_ok=True)

        # Load Haar cascade for face detection
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(f"Haar cascade not found at {cascade_path}")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

    def process_frame(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30)
        )
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        return frame, {"faces_detected": len(faces)}

    def merge_audio(self, original_video, annotated_video):
        temp_output = annotated_video.replace(".mp4", "_with_audio.mp4")
        command = [
            "ffmpeg",
            "-y",
            "-i", annotated_video,
            "-i", original_video,
            "-c:v", "copy",
            "-c:a", "aac",
            "-map", "0:v:0",
            "-map", "1:a:0?",
            temp_output
        ]
        try:
            subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            os.replace(temp_output, annotated_video)
            print(f"[INFO] Audio merged into: {annotated_video}")
        except subprocess.CalledProcessError as e:
            print(f"[WARNING] Audio merge failed: {e}")

    def process_video(self, video_path):
        video_path = os.path.abspath(video_path)
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file does not exist: {video_path}")

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise IOError(f"Cannot open video: {video_path}")

        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or float(os.getenv("PROCESSED_FPS", 20.0))
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")

        # Save annotated video in the separate folder
        base_name = os.path.splitext(os.path.basename(video_path))[0] + "_annotated.mp4"
        output_path = os.path.join(self.annotated_folder, base_name)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        report = []

        print(f"[INFO] Processing video: {video_path}")
        frame_idx = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            try:
                annotated_frame, res = self.process_frame(frame)
            except Exception as e:
                print(f"[WARNING] Frame processing error: {e}")
                annotated_frame = frame
                res = {}

            res["timestamp_sec"] = round(frame_idx / fps, 2)
            frame_idx += 1

            out.write(annotated_frame)
            report.append(res)

        cap.release()
        out.release()

        # Merge original audio
        self.merge_audio(video_path, output_path)

        print(f"[INFO] Processing complete. Saved to: {output_path}")
        return output_path, report
