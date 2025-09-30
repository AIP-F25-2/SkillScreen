# import av
# import whisper
# import requests
# import os
# import uuid
# import tempfile

# # Load the base Whisper model. It will be downloaded on the first run.
# model = whisper.load_model("base")

# def process_video_for_analysis(video_urls: list[str]):
#     """
#     Downloads a list of videos, extracts audio, and performs speech-to-text transcription
#     and analysis on each.
#     """
#     video_breakdown = []
    
#     # Get the system's default temporary directory for cross-platform compatibility
#     temp_dir = tempfile.gettempdir()
    
#     for url in video_urls:
#         temp_video_path = ""
#         temp_audio_path = ""
#         try:
#             # 1. Download the video from the URL
#             print(f"Downloading video from {url}...")
#             video_filename = f"{uuid.uuid4()}.mp4"
#             temp_video_path = os.path.join(temp_dir, video_filename)
            
#             with requests.get(url, stream=True) as r:
#                 r.raise_for_status()
#                 with open(temp_video_path, 'wb') as f:
#                     for chunk in r.iter_content(chunk_size=8192):
#                         f.write(chunk)

#             # 2. Extract audio from the video using PyAV
#             print("Extracting audio with PyAV...")
#             audio_filename = f"{uuid.uuid4()}.wav"
#             temp_audio_path = os.path.join(temp_dir, audio_filename)
#             with av.open(temp_video_path) as video_container:
#                 audio_stream = video_container.streams.get(audio=0)[0]
#                 with av.open(temp_audio_path, 'w') as audio_container:
#                     output_stream = audio_container.add_stream('pcm_s16le', rate=16000)
#                     for frame in video_container.decode(audio_stream):
#                         for packet in output_stream.encode(frame):
#                             audio_container.mux(packet)

#             # 3. Transcribe the audio using Whisper with word-level timestamps for accuracy
#             print("Transcribing audio with word-level detail...")
#             result = model.transcribe(temp_audio_path, word_timestamps=True, fp16=False,condition_on_previous_text=False,logprob_threshold=None)
#             transcript_text = result["text"]

#             # 4. Calculate Analytics from the detailed transcription result
#             # Speaking Pace (Words Per Minute)
#             num_words = len(transcript_text.split())
#             duration_seconds = result['segments'][-1]['end'] if result.get('segments') else 0
#             wpm = (num_words / duration_seconds) * 60 if duration_seconds > 0 else 0

#             # Accurate Filler Word Count from word-level data
#             filler_words = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'you know', 'so', 'oh']
#             filler_word_count = 0
#             if result.get('segments'):
#                 for segment in result['segments']:
#                     for word_data in segment['words']:
#                         word = word_data['word'].strip(".,?!").lower()
#                         if word in filler_words:
#                             filler_word_count += 1
            
#             analytics_data = {
#                 "speakingPaceWPM": round(wpm),
#                 "wordCount": num_words,
#                 "fillerWordCount": filler_word_count,
#                 "speechDurationSeconds": round(duration_seconds, 2)
#             }
            
#             # Append the full result for this video
#             video_breakdown.append({
#                 "sourceVideoUrl": url,
#                 "transcript": transcript_text,
#                 "analytics": analytics_data
#             })

#         except Exception as e:
#             print(f"Error processing {url}: {e}")
#             video_breakdown.append({"sourceVideoUrl": url, "error": str(e)})
#         finally:
#             # 5. Clean up temporary files
#             print("Cleaning up...")
#             if os.path.exists(temp_video_path):
#                 os.remove(temp_video_path)
#             if os.path.exists(temp_audio_path):
#                 os.remove(temp_audio_path)

#     return {"analysisId": f"real-{uuid.uuid4()}", "videoBreakdown": video_breakdown}

#whisperx code below

# import whisperx
# import requests
# import os
# import uuid
# import tempfile
# import av

# # --- WhisperX Model Setup ---
# # This runs once when the service starts up.
# # Using "int8" compute_type is faster and uses less memory on CPU.
# device = "cpu"
# compute_type = "int8"
# model = whisperx.load_model("base", device, compute_type=compute_type)


# def process_video_for_analysis(video_urls: list[str]):
#     """
#     Downloads videos, extracts audio, and performs a detailed, literal transcription
#     and analysis using WhisperX.
#     """
#     video_breakdown = []
#     temp_dir = tempfile.gettempdir()
    
#     for url in video_urls:
#         temp_video_path = ""
#         temp_audio_path = ""
#         try:
#             # --- 1. Download and Extract Audio ---
#             print(f"Downloading video from {url}...")
#             video_filename = f"{uuid.uuid4()}.mp4"
#             temp_video_path = os.path.join(temp_dir, video_filename)
            
#             with requests.get(url, stream=True) as r:
#                 r.raise_for_status()
#                 with open(temp_video_path, 'wb') as f:
#                     for chunk in r.iter_content(chunk_size=8192):
#                         f.write(chunk)

#             print("Extracting audio with PyAV...")
#             audio_filename = f"{uuid.uuid4()}.wav"
#             temp_audio_path = os.path.join(temp_dir, audio_filename)
#             with av.open(temp_video_path) as video_container:
#                 audio_stream = video_container.streams.get(audio=0)[0]
#                 with av.open(temp_audio_path, 'w') as audio_container:
#                     output_stream = audio_container.add_stream('pcm_s16le', rate=16000)
#                     for frame in video_container.decode(audio_stream):
#                         for packet in output_stream.encode(frame):
#                             audio_container.mux(packet)

#             # --- 2. Transcribe and Align with WhisperX ---
#             print("Loading audio for WhisperX...")
#             audio = whisperx.load_audio(temp_audio_path)
            
#             print("Transcribing with WhisperX...")
#             result = model.transcribe(audio, batch_size=16)

#             print("Aligning transcript for word-level detail...")
#             model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
#             aligned_result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

#             # --- 3. Calculate Analytics from the Raw Transcript ---
#             transcript_text = " ".join([segment['text'].strip() for segment in aligned_result["segments"]])
            
#             word_segments = aligned_result.get('word_segments', [])
#             num_words = len(word_segments)
#             duration_seconds = word_segments[-1]['end'] if num_words > 0 else 0
#             wpm = (num_words / duration_seconds) * 60 if duration_seconds > 0 else 0

#             # Accurate Filler Word Count and breakdown
#             filler_words = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'you know', 'so', 'oh']
#             filler_word_counts = {word: 0 for word in filler_words}
#             total_filler_count = 0

#             for word_data in word_segments:
#                 word = word_data['word'].strip(".,?!").lower()
#                 if word in filler_words:
#                     filler_word_counts[word] += 1
#                     total_filler_count += 1
            
#             final_filler_breakdown = {word: count for word, count in filler_word_counts.items() if count > 0}

#             analytics_data = {
#                 "speakingPaceWPM": round(wpm),
#                 "wordCount": num_words,
#                 "totalFillerCount": total_filler_count,
#                 "fillerWordBreakdown": final_filler_breakdown,
#                 "speechDurationSeconds": round(duration_seconds, 2)
#             }
            
#             video_breakdown.append({
#                 "sourceVideoUrl": url,
#                 "transcript": transcript_text,
#                 "analytics": analytics_data
#             })

#         except Exception as e:
#             print(f"Error processing {url}: {e}")
#             video_breakdown.append({"sourceVideoUrl": url, "error": str(e)})
#         finally:
#             # --- 4. Cleanup ---
#             print("Cleaning up temporary files...")
#             if os.path.exists(temp_video_path):
#                 os.remove(temp_video_path)
#             if os.path.exists(temp_audio_path):
#                 os.remove(temp_audio_path)

#     return {"analysisId": f"whisperx-{uuid.uuid4()}", "videoBreakdown": video_breakdown}

#VOSK code below

import requests
import os
import uuid
import tempfile
import av
import wave
import json
from vosk import Model, KaldiRecognizer

# --- Vosk Model Setup ---
# This runs once when the service starts.
# IMPORTANT: Update this path to the exact name of the model folder you downloaded.
model_path = "vosk-model-en-us-0.22"
if not os.path.exists(model_path):
    raise FileNotFoundError(
        f"Vosk model not found at '{model_path}'. "
        "Please download the model, unzip it, and place the folder in your project's root directory."
    )
model = Model(model_path)


def process_video_for_analysis(video_urls: list[str]):
    """
    Downloads a list of videos, extracts audio, and performs a literal speech-to-text
    transcription and analysis on each using the Vosk toolkit.
    """
    video_breakdown = []
    temp_dir = tempfile.gettempdir()
    
    for url in video_urls:
        temp_video_path = ""
        temp_audio_path = ""
        try:
            # --- 1. Download and Extract Audio ---
            print(f"Downloading video from {url}...")
            video_filename = f"{uuid.uuid4()}.mp4"
            temp_video_path = os.path.join(temp_dir, video_filename)
            
            with requests.get(url, stream=True) as r:
                r.raise_for_status()
                with open(temp_video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            print("Extracting audio with PyAV...")
            audio_filename = f"{uuid.uuid4()}.wav"
            temp_audio_path = os.path.join(temp_dir, audio_filename)
            with av.open(temp_video_path) as video_container:
                audio_stream = video_container.streams.get(audio=0)[0]
                with av.open(temp_audio_path, 'w') as audio_container:
                    output_stream = audio_container.add_stream('pcm_s16le', rate=16000)
                    for frame in video_container.decode(audio_stream):
                        for packet in output_stream.encode(frame):
                            audio_container.mux(packet)

            # --- 2. Transcribe with Vosk ---
            print("Transcribing with Vosk...")
            wf = wave.open(temp_audio_path, "rb")
            rec = KaldiRecognizer(model, wf.getframerate())
            rec.SetWords(True)  # Tell Vosk to return word-level details

            # Process audio in chunks
            while True:
                data = wf.readframes(4000)
                if len(data) == 0:
                    break
                rec.AcceptWaveform(data)
            
            wf.close()
            result = json.loads(rec.FinalResult())
            transcript_text = result.get('text', '')
            word_segments = result.get('result', [])

            # --- 3. Calculate Analytics from the Raw Transcript ---
            num_words = len(word_segments)
            duration_seconds = word_segments[-1]['end'] if num_words > 0 else 0
            wpm = (num_words / duration_seconds) * 60 if duration_seconds > 0 else 0

            filler_words = ['um', 'uh', 'er', 'ah', 'like', 'okay', 'right', 'you know', 'so', 'oh']
            filler_word_counts = {word: 0 for word in filler_words}
            total_filler_count = 0

            for word_data in word_segments:
                word = word_data.get('word', '').strip(".,?!").lower()
                if word in filler_words:
                    filler_word_counts[word] += 1
                    total_filler_count += 1
            
            final_filler_breakdown = {word: count for word, count in filler_word_counts.items() if count > 0}

            analytics_data = {
                "speakingPaceWPM": round(wpm),
                "wordCount": num_words,
                "totalFillerCount": total_filler_count,
                "fillerWordBreakdown": final_filler_breakdown,
                "speechDurationSeconds": round(duration_seconds, 2)
            }
            
            video_breakdown.append({
                "sourceVideoUrl": url,
                "transcript": transcript_text,
                "analytics": analytics_data
            })

        except Exception as e:
            print(f"Error processing {url}: {e}")
            video_breakdown.append({"sourceVideoUrl": url, "error": str(e)})
        finally:
            # --- 4. Cleanup ---
            print("Cleaning up temporary files...")
            if os.path.exists(temp_video_path):
                os.remove(temp_video_path)
            if os.path.exists(temp_audio_path):
                os.remove(temp_audio_path)

    return {"analysisId": f"vosk-{uuid.uuid4()}", "videoBreakdown": video_breakdown}