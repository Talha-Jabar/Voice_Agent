import sounddevice as sd
import numpy as np
import wave
from pydub import AudioSegment, silence
import os

class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1, silence_thresh=-16, min_silence_len=500):
        self.sample_rate = sample_rate
        self.channels = channels
        self.silence_thresh = silence_thresh   # in dB
        self.min_silence_len = min_silence_len  # in ms
        self.max_retries = 3
        # Removed unused attributes: recording, audio_data

    def record_audio(self, duration=5, filename="user_input.wav"):
        """Record audio for a specified duration and save to file"""
        print(f"Recording for {duration} seconds...")
        
        audio_data = sd.rec(int(duration * self.sample_rate), 
                           samplerate=self.sample_rate, 
                           channels=self.channels, 
                           dtype=np.int16)
        sd.wait()
        
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        print(f"Audio saved to {filename}")
        return filename
    
    def is_silent(self, filename):
        """Check if audio file is silent using pydub"""
        audio = AudioSegment.from_wav(filename)
        non_silent_ranges = silence.detect_nonsilent(
            audio,
            min_silence_len=self.min_silence_len,
            silence_thresh=self.silence_thresh
        )
        return len(non_silent_ranges) == 0

    def record_until_silence(self, filename="user_input.wav", rms_silence_threshold=0.01, silence_duration=3, max_duration=5):
        """Record until silence is detected, retry if completely silent"""
        retries = 0
        while retries < self.max_retries:
            print(f"Recording attempt {retries+1} of {self.max_retries}... Speak now.")
        
            chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks
            audio_chunks = []
            silence_counter = 0
            silence_chunks_needed = int(silence_duration / 0.1)
            max_chunks = int(max_duration / 0.1)
            chunk_count = 0
        
            try:
                with sd.InputStream(samplerate=self.sample_rate, 
                                channels=self.channels, 
                                dtype=np.float32) as stream:
                    while True:
                        chunk, overflowed = stream.read(chunk_size)
                        if overflowed:
                            print("Warning: Audio overflow")
                        audio_chunks.append(chunk.copy())
                        chunk_count += 1
                        
                        # Check for silence using RMS
                        rms = np.sqrt(np.mean(chunk**2))
                        if rms < rms_silence_threshold:
                            silence_counter += 1
                        else:
                            silence_counter = 0
                        
                        # Check stop conditions
                        if silence_counter >= silence_chunks_needed:
                            print(f"Silence detected for {silence_duration}s, stopping recording.")
                            break
                            
                        if chunk_count >= max_chunks:
                            print(f"Max duration ({max_duration}s) reached, stopping recording.")
                            break
                            
            except KeyboardInterrupt:
                print("\nRecording stopped by user")
                break
            
            if audio_chunks:
                audio_data = np.concatenate(audio_chunks)
                # Convert to int16 for WAV
                audio_data_int16 = (audio_data * 32767).astype(np.int16)
                
                with wave.open(filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(2)
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(audio_data_int16.tobytes())
                
                if self.is_silent(filename):
                    retries += 1
                    print("No voice detected. Please try again.")
                    continue
                else:
                    print(f"Audio saved to {filename}")
                    return filename
            else:
                retries += 1
                print("No audio captured. Please try again.")

        print("No valid audio detected after 3 attempts. Terminating process.")
        return None
    

