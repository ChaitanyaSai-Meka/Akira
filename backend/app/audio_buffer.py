import numpy as np

class AudioBuffer:
    def __init__(self, frame_size: int = 320):
        self.frame_size = frame_size
        self.buffer = np.zeros(0, dtype=np.int16)

    def add_samples(self, samples: np.ndarray):
        """
        Add new audio samples to the buffer
        """
        if samples.dtype != np.int16:
            raise ValueError("AudioBuffer expects int16 samples")

        self.buffer = np.concatenate((self.buffer, samples))

    def has_frame(self) -> bool:
        """
        Check if at least one full frame is available
        """
        return len(self.buffer) >= self.frame_size

    def get_frame(self) -> np.ndarray:
        """
        Return exactly one frame of audio (frame_size samples)
        """
        if not self.has_frame():
            raise RuntimeError("Not enough samples for a full frame")

        frame = self.buffer[:self.frame_size]
        self.buffer = self.buffer[self.frame_size:]
        return frame
