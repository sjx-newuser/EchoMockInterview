import subprocess
import os

# Generate a 1s sample webm buffer
cmd = ["ffmpeg", "-y", "-f", "lavfi", "-i", "sine=frequency=1000:duration=1", "-c:a", "libopus", "-f", "webm", "pipe:1"]
p1 = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
webm_bytes, _ = p1.communicate()

print(f"Generated {len(webm_bytes)} bytes of WebM data.")

cmd2 = ["ffmpeg", "-y", "-i", "pipe:0", "-f", "wav", "-ac", "1", "-ar", "16000", "pipe:1"]
p2 = subprocess.Popen(cmd2, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
wav_data, stderr_data = p2.communicate(input=webm_bytes)

if p2.returncode != 0:
    print(f"FAILED: {stderr_data.decode()}")
else:
    print(f"SUCCESS: converted to {len(wav_data)} bytes of WAV")
