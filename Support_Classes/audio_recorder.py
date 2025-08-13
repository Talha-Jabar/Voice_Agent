import sounddevice as sd
import numpy as np
import wave
import os

class AudioRecorder:
    def __init__(self, sample_rate=44100, channels=1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.recording = False
        self.audio_data = []

    def record_audio(self, duration=10, filename="user_input.wav"):
        """Record audio for a specified duration and save to file"""
        print(f"Recording for {duration} seconds...")
        
        # Record audio
        audio_data = sd.rec(int(duration * self.sample_rate), 
                           samplerate=self.sample_rate, 
                           channels=self.channels, 
                           dtype=np.int16)
        sd.wait()  # Wait until recording is finished
        
        # Save to WAV file
        with wave.open(filename, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_data.tobytes())
        
        print(f"Audio saved to {filename}")
        return filename

    def record_until_silence(self, filename="user_input.wav", silence_threshold=0.01, silence_duration=4):
        """Record audio until silence is detected"""
        print("Recording... (speak now, will stop after silence)")
        
        chunk_size = int(self.sample_rate * 0.1)  # 100ms chunks
        audio_chunks = []
        silence_counter = 0
        silence_chunks_needed = int(silence_duration / 0.1)
        
        try:
            with sd.InputStream(samplerate=self.sample_rate, 
                              channels=self.channels, 
                              dtype=np.float32) as stream:
                while True:
                    chunk, _ = stream.read(chunk_size)
                    audio_chunks.append(chunk)
                    
                    # Check for silence
                    volume = np.sqrt(np.mean(chunk**2))
                    if volume < silence_threshold:
                        silence_counter += 1
                    else:
                        silence_counter = 0
                    
                    # Stop if silence detected for specified duration
                    if silence_counter >= silence_chunks_needed:
                        break
                        
        except KeyboardInterrupt:
            print("\nRecording stopped by user")
        
        # Combine all chunks
        if audio_chunks:
            audio_data = np.concatenate(audio_chunks)
            # Convert to int16 for WAV file
            audio_data_int16 = (audio_data * 32767).astype(np.int16)
            
            # Save to WAV file
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data_int16.tobytes())
            
            print(f"Audio saved to {filename}")
            return filename
        
        return None

