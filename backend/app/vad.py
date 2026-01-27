import numpy as np


class VAD:
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_size: int = 320,
        energy_ratio: float = 1.2,
        min_speech_frames: int = 2,
        min_silence_frames: int = 30,
        alpha: float = 0.95
    ):
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.energy_ratio = energy_ratio
        self.alpha = alpha
        self.min_speech_frames = min_speech_frames
        self.min_silence_frames = min_silence_frames
        self.noise_rms = 0.0
        self.speech_frames = 0
        self.silence_frames = 0
        self.in_speech = False
        self.pre_emphasis = 0.97
        self.prev_sample = 0.0
        self.freqs = np.fft.rfftfreq(frame_size, 1 / sample_rate)
        self.speech_band = np.where(
            (self.freqs >= 300) & (self.freqs <= 3400)
        )[0]

    def _pre_emphasis(self, frame):
        emphasized = np.empty_like(frame, dtype=np.float32)
        emphasized[0] = frame[0] - self.pre_emphasis * self.prev_sample
        emphasized[1:] = frame[1:] - self.pre_emphasis * frame[:-1]
        self.prev_sample = frame[-1]
        return emphasized

    def _rms(self, frame):
        return np.sqrt(np.mean(frame ** 2) + 1e-8)

    def _zcr(self, frame):
        return np.mean(np.abs(np.diff(np.sign(frame)))) / 2

    def _band_energy_ratio(self, mag):
        band_energy = np.sum(mag[self.speech_band])
        total_energy = np.sum(mag) + 1e-8
        return band_energy / total_energy

    def _spectral_flatness(self, mag):
        mag = mag + 1e-8
        return np.exp(np.mean(np.log(mag))) / np.mean(mag)

    def process(self, frame: np.ndarray) -> str:
        frame = frame.astype(np.float32)
        frame = self._pre_emphasis(frame)

        rms = self._rms(frame)
        zcr = self._zcr(frame)

        spectrum = np.fft.rfft(frame * np.hanning(len(frame)))
        mag = np.abs(spectrum)

        band_ratio = self._band_energy_ratio(mag)
        flatness = self._spectral_flatness(mag)

        if self.noise_rms == 0.0:
            self.noise_rms = rms * 0.5
            return "silence"

        energy_ok = rms > self.noise_rms * self.energy_ratio
        continue_energy_ok = rms > self.noise_rms * 0.85
        zcr_ok = zcr > 0.008
        band_ok = band_ratio > 0.30

        start_speech = (
            energy_ok and
            (band_ok or zcr_ok)
        )

        continue_speech = continue_energy_ok

        if not self.in_speech and rms < self.noise_rms * 1.2:
            self.noise_rms = (
                self.alpha * self.noise_rms +
                (1 - self.alpha) * rms
            )

        if start_speech or (self.in_speech and continue_speech):
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
