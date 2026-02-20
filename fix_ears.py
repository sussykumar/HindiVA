import urllib.request
import zipfile
import os
import shutil

url = "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip"
zip_path = "vosk_temp.zip"
extract_dir = "temp_extract"
target_dir = "model"

print("\n" + "="*50)
print("🎧 DOWNLOADING CLEAN VOSK HINDI MODEL (42MB)...")
print("="*50)

# 1. Download the zip
try:
    urllib.request.urlretrieve(url, zip_path)
    print("✅ Download complete.")
except Exception as e:
    print(f"❌ Download failed: {e}")
    exit(1)

# 2. Extract safely using Python's native library
print("📦 Extracting files safely (bypassing Windows)...")
with zipfile.ZipFile(zip_path, 'r') as zip_ref:
    zip_ref.extractall(extract_dir)

# 3. Locate the inner folder and move it to the root 'model'
inner_folder = os.path.join(extract_dir, "vosk-model-small-hi-0.22")

if os.path.exists(target_dir):
    shutil.rmtree(target_dir)

os.rename(inner_folder, target_dir)

# 4. Clean up the mess
os.remove(zip_path)
shutil.rmtree(extract_dir)

print("✨ SUCCESS! The 'model' folder is now perfectly structured and uncorrupted.\n")