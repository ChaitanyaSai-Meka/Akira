import numpy as np


class VAD:
    """
    Adaptive Voice Activity Detector (VAD)

    Uses:
    - Relative RMS energy (adaptive noise floor)
    - Relative Zero Crossing Rate (adaptive)
    - Temporal smoothing (minimum speech duration)
    - Hysteresis (stable start / end detection)
    """

    def __init__(
        self,
        energy_ratio: float = 3.0,
        zcr_ratio: float = 1.5,
        min_speech_frames: int = 4,  
        min_silence_frames: int = 8,  
        alpha: float = 0.95           
    ):
    
        self.rms_floor = 0.0
        self.zcr_floor = 0.0
        self.alpha = alpha

    
        self.energy_ratio = energy_ratio
        self.zcr_ratio = zcr_ratio

    
        self.min_speech_frames = min_speech_frames
        self.min_silence_frames = min_silence_frames

        self.speech_frames = 0
        self.silence_frames = 0
        self.in_speech = False


    def _rms(self, frame: np.ndarray) -> float:
        return np.sqrt(np.mean(frame.astype(np.float32) ** 2))

    def _zcr(self, frame: np.ndarray) -> float:
        return np.mean(np.abs(np.diff(np.sign(frame))))


    def process(self, frame: np.ndarray) -> str:
        """
        Process one audio frame.

        Returns one of:
        - "silence"
        - "speech_start"
        - "speech"
        - "speech_end"
        """

        rms = self._rms(frame)
        zcr = self._zcr(frame)

    
        if self.rms_floor == 0.0:
            self.rms_floor = rms
            self.zcr_floor = zcr
            return "silence"

    
        is_speech_frame = (
            rms > self.rms_floor * self.energy_ratio and
            zcr > self.zcr_floor * self.zcr_ratio
        )

    
        if not is_speech_frame:
            self.rms_floor = (
                self.alpha * self.rms_floor +
                (1 - self.alpha) * rms
            )
            self.zcr_floor = (
                self.alpha * self.zcr_floor +
                (1 - self.alpha) * zcr
            )

    
        if is_speech_frame:
            self.speech_frames += 1
            self.silence_frames = 0

        
            if not self.in_speech and self.speech_frames >= self.min_speech_frames:
                self.in_speech = True
                return "speech_start"

            if self.in_speech:
                return "speech"

        else:
            self.silence_frames += 1
            self.speech_frames = 0

            if self.in_speech and self.silence_frames >= self.min_silence_frames:
                self.in_speech = False
                return "speech_end"

        return "silence"
