import numpy as np
from scipy.signal import butter, lfilter

class NoiseSuppressor:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

        self.b, self.a = self._create_bandpass(300, 3400, sample_rate)
        self.zi = np.zeros(max(len(self.a), len(self.b)) - 1)

        self.noise_floor = 0.0
        self.alpha = 0.95  

        self.speech_ratio = 3.0

    def _create_bandpass(self, lowcut, highcut, fs, order=5):
        nyq = 0.5 * fs
        return butter(order, [lowcut/nyq, highcut/nyq], btype="band")

    def process(self, frame: np.ndarray) -> tuple[np.ndarray, bool]:
        filtered, self.zi = lfilter(self.b, self.a, frame, zi=self.zi)

        rms = np.sqrt(np.mean(filtered ** 2))

        if self.noise_floor == 0:
            self.noise_floor = rms

        is_speech = rms > self.noise_floor * self.speech_ratio

        if not is_speech:
            self.noise_floor = (
                self.alpha * self.noise_floor +
                (1 - self.alpha) * rms
            )

        if not is_speech:
            filtered[:] = 0

        return filtered.astype(np.int16), is_speech
