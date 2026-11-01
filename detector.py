
import mediapipe as mp


class DetectorMaos:

    def __init__(self):

        BaseOptions = mp.tasks.BaseOptions
        HandLandmarker = mp.tasks.vision.HandLandmarker
        HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
        RunningMode = mp.tasks.vision.RunningMode

        options = HandLandmarkerOptions(
            base_options=BaseOptions(
                model_asset_path="hand_landmarker.task"
            ),
            running_mode=RunningMode.VIDEO,
            num_hands=2
        )

        self.detector = HandLandmarker.create_from_options(options)

    def detectar(self, frame, timestamp):

        imagem = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=frame
        )

        resultado = self.detector.detect_for_video(
            imagem,
            timestamp
        )

        return resultado

    def fechar(self):
        self.detector.close()
