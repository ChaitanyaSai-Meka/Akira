import numpy as np


class NoiseSuppressor:
    def __init__(self, alpha=0.95):
        self.alpha = alpha
        self.noise_mag = None

    def process(self, frame):
        frame = frame.astype(np.float32)
        spectrum = np.fft.rfft(frame)
        mag = np.abs(spectrum)
        phase = np.angle(spectrum)

        if self.noise_mag is None:
            self.noise_mag = mag
            return frame.astype(np.int16)

        self.noise_mag = (
            self.alpha * self.noise_mag +
            (1 - self.alpha) * mag
        )

        clean_mag = np.maximum(mag - self.noise_mag, 0.0)
        clean_spec = clean_mag * np.exp(1j * phase)
        clean_frame = np.fft.irfft(clean_spec)
        
        clean_frame = np.clip(clean_frame, -32768, 32767)
        return clean_frame.astype(np.int16)
