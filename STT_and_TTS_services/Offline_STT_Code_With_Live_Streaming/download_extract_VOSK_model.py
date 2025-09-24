import os
import requests
import zipfile

# --- Configuration ---
model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
models_dir = "models"
model_name = "vosk-model-small-en-us-0.15"
zip_path = os.path.join(models_dir, f"{model_name}.zip")

# --- Create models directory if not exists ---
os.makedirs(models_dir, exist_ok=True)

# --- Download the model ---
if not os.path.exists(zip_path):
    print(f"Downloading {model_name}...")
    response = requests.get(model_url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    downloaded = 0
    with open(zip_path, "wb") as f:
        for data in response.iter_content(chunk_size=1024*1024):
            f.write(data)
            downloaded += len(data)
            print(f"\rDownloaded {downloaded/1024/1024:.2f} MB / {total_size/1024/1024:.2f} MB", end="")
    print("\nDownload complete!")

# --- Extract the model ---
model_path = os.path.join(models_dir, model_name)
if not os.path.exists(model_path):
    print(f"Extracting {model_name}...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(models_dir)
    print("Extraction complete!")

print(f"Model ready at: {model_path}")
