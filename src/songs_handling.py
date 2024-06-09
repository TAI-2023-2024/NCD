import subprocess
import time
import os


class AudioProcessor:
    def __init__(self, input_audio, output_audio):
        self.input_audio = input_audio
        self.output_audio = output_audio
        
    def _get_audio_properties(self):
        """
        Get the sample rate and number of channels of an audio file using SoX.
        
        Parameters:
        - file_path: Path to the audio file.
        
        Returns:
        - sample_rate: Sample rate of the audio file.
        - channels: Number of channels in the audio file.
        """
        
        result = subprocess.run(['sox', '--i', '-r', self.input_audio], capture_output=True, text=True)
        sample_rate = result.stdout.strip()
        result = subprocess.run(['sox', '--i', '-c', self.input_audio], capture_output=True, text=True)
        channels = result.stdout.strip()
        return sample_rate, channels
    
    def _get_audio_duration(self):
        """
        Get the duration of an audio file using SoX.

        Returns:
        - duration: Duration of the audio file in seconds.
        """
        result = subprocess.run(['sox', '--i', '-D', self.input_audio], capture_output=True, text=True)
        duration = float(result.stdout.strip())
        return duration

    def _extract_segment(self, start_time, duration=10):
        """
        Extract a segment from an audio file using SoX.

        Parameters:
        - input_file: Path to the input audio file.
        - output_file: Path to save the extracted segment.
        - start_time: Start time of the segment (in seconds).
        - duration: Duration of the segment (default is 10 seconds).
        """
        try:
            subprocess.run(['sox', self.input_audio, self.output_audio, 'trim', str(start_time), str(duration)], check=True)
            print(f"Extracted segment from {start_time}s to {start_time + duration}s and saved to {self.output_audio}")
        except subprocess.CalledProcessError as e:
            print(f"Error during segment extraction: {e}")

    def _add_noise(self, noise_duration=10, noise_level=0.05):
        """
        Add noise to an audio file using SoX.

        Parameters:
        - input_file: Path to the input audio file.
        - output_file: Path to save the output audio file with noise.
        - noise_duration: Duration of the noise to generate in seconds (default is 10).
        - noise_level: Level of noise to add (default is 0.05).
        """
        try:
            start_time = time.time()

            # Ensure the output directory exists
            output_dir = os.path.dirname(self.output_audio)
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            # Get sample rate and channels of the input file
            sample_rate, channels = self._get_audio_properties()
            
            # Generate the noise file
            noise_file = 'whitenoise.wav'
            print("Generating noise...")
            #subprocess.run(['sox', '-n', '-r', sample_rate, '-c', channels, noise_file, 'synth', str(noise_duration), 'whitenoise', 'vol', '0.3'], check=True)
            subprocess.run(['sox', '-n', '-r', sample_rate, '-c', channels, noise_file, 'synth', str(noise_duration), 'whitenoise', 'vol', str(noise_level)], check=True)

            # Mix noise with the original audio
            print("Mixing noise with original audio...")
            #subprocess.run(['sox', '-m', self.input_audio, noise_file, self.output_audio, 'vol', str(noise_level)], check=True)
            subprocess.run(['sox', '-m', self.input_audio, noise_file, self.output_audio], check=True)

            # Clean up the noise file
            print("Cleaning up...")
            os.remove(noise_file)

            end_time = time.time()
            print(f"Process completed in {end_time - start_time:.2f} seconds.")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            print("Ensure SoX is installed and added to the system's PATH.")
        except subprocess.CalledProcessError as e:
            print(f"Error during processing: {e}")

class DatabaseProcessor:
    def __init__(self, database_dir, output_dir, segment_duration=10, noise_level=0.70):
        self.database_dir = database_dir
        self.output_dir = output_dir
        self.segment_duration = segment_duration
        self.noise_level = noise_level

    def process_database(self):
        """
        Process all audio files in the database to extract segments and add noise.
        """
        for root, _, files in os.walk(self.database_dir):
            for file in files:
                if file.endswith('.wav'): 
                    input_file = os.path.join(root, file)
                    file_name, _ = os.path.splitext(file)
                    
                    processor = AudioProcessor(input_file, None)
                    duration = processor._get_audio_duration()
                    
                    # Extract segments from the audio file
                    segment_output_dir = os.path.join(self.output_dir, 'Segments', file_name)
                    if not os.path.exists(segment_output_dir):
                        os.makedirs(segment_output_dir)
                    
                    # Extract segments from the file, based on its duration
                    segment_start_times = range(0, int(duration), self.segment_duration)
                    for start_time in segment_start_times:
                        if duration - start_time < self.segment_duration:
                            print(f"Skipping segment from {start_time}s as it is shorter than {self.segment_duration}s")
                            continue

                        segment_output_file = os.path.join(segment_output_dir, f"{file_name}_segment_{start_time}-{start_time + self.segment_duration}.wav")
                        processor.output_audio = segment_output_file
                        processor._extract_segment(start_time=start_time, duration=min(self.segment_duration, duration - start_time))
                        
                        # Add noise to the segment
                        noised_output_dir = os.path.join(self.output_dir, 'Noised', file_name)
                        if not os.path.exists(noised_output_dir):
                            os.makedirs(noised_output_dir)
                        
                        noised_output_file = os.path.join(noised_output_dir, f"{file_name}_segment_{start_time}-{start_time + self.segment_duration}_noised.wav")
                        noise_processor = AudioProcessor(segment_output_file, noised_output_file)
                        noise_processor._add_noise(noise_duration=min(self.segment_duration, duration - start_time), noise_level=self.noise_level)

# Example usage
database_directory = '../Data/Database'
output_directory = '../Data/Processed'

db_processor = DatabaseProcessor(database_directory, output_directory, segment_duration=10, noise_level=0.70)
db_processor.process_database()
