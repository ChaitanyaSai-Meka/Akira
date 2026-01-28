import numpy as np
import webrtcvad
import struct


class VAD:
    def __init__(
        self,
        sample_rate: int = 16000,
        frame_size: int = 320,
        aggressiveness: int = 3,
        min_speech_frames: int = 8,
        min_silence_frames: int = 30,
    ):
        self.sample_rate = sample_rate
        self.frame_size = frame_size
        self.min_speech_frames = min_speech_frames
        self.min_silence_frames = min_silence_frames
        
        self.vad = webrtcvad.Vad(aggressiveness)
        
        self.speech_frames = 0
        self.silence_frames = 0
        self.in_speech = False
        self.energy_threshold = 100.0
        self.noise_floor = 0.0
        self.noise_floor_initialized = False

    def _calculate_energy(self, frame: np.ndarray) -> float:
        return np.sqrt(np.mean(frame.astype(np.float32) ** 2))

    def process(self, frame: np.ndarray) -> str:
        if len(frame) != self.frame_size:
            raise ValueError(f"Expected frame size {self.frame_size}, got {len(frame)}")

        energy = self._calculate_energy(frame)
        
        if not self.noise_floor_initialized:
            self.noise_floor = energy
            self.noise_floor_initialized = True
            return "silence"
        
        if not self.in_speech and energy < self.noise_floor * 1.5:
            self.noise_floor = 0.95 * self.noise_floor + 0.05 * energy

        frame_bytes = struct.pack(f'{len(frame)}h', *frame.astype(np.int16))
        
        try:
            is_speech = self.vad.is_speech(frame_bytes, self.sample_rate)
        except Exception:
            return "silence"
        
        has_energy = energy > max(self.energy_threshold, self.noise_floor * 2.0)
        
        speech_detected = is_speech and has_energy
        
        if speech_detected:
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
