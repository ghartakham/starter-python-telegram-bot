import os
import threading
import requests
from pydub import AudioSegment
from pydub.utils import mediainfo
from hashlib import md5
from landr import *

def generate_md5_hash(filename, length=16):
    hasher = md5()
    with open(filename, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()[:length]

def split_audio(filename):
    chunks = []
    hash_code = generate_md5_hash(filename)

    file_info = mediainfo(filename)
    original_bitrate = file_info['bit_rate']

    audio = AudioSegment.from_mp3(filename)

    chunk_length_ms = 30000

    for i in range(0, len(audio), chunk_length_ms):
        edge_ms = min(i + chunk_length_ms, len(audio))
        
        chunk_filename = f"{int(edge_ms / 1000)}_{hash_code}.mp3"
        
        chunk = audio[i:edge_ms]
        chunk.export(chunk_filename, format="mp3", bitrate=original_bitrate)
        chunks.append(chunk_filename)
    return chunks

def merge_audio(chunks, output_filename, original_bitrate):
    combined = AudioSegment.empty()
    for chunk in chunks:
        audio_chunk = AudioSegment.from_mp3(chunk)
        combined += audio_chunk
    combined.export(output_filename, format="mp3", bitrate=original_bitrate)


max_threads = threading.Semaphore(3)

def master_chunk(chunk, volume, style):
    max_threads.acquire()
    try:        
        upload_id, asset_id, etag = upload_file(chunk)
        max_threads.release()
        complete_upload(upload_id, etag)
        samples = get_mastering_samples(asset_id)
        for sample in samples:
            if sample['intensity'] == volume and sample['style'] == style:
                content = requests.get(sample['mp3Url']).content
                with open(chunk, 'wb') as f:
                    f.write(content)
        delete_asset(asset_id)
    finally:
        pass

def master_track(file_name_in, file_name_out, volume='Medium', style='PS2'):
    file_info = mediainfo(file_name_in)
    original_bitrate = file_info['bit_rate']

    chunks = split_audio(file_name_in)

    threads = []

    for chunk in chunks:
        thread = threading.Thread(target=master_chunk, args=(chunk, volume, style,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    merge_audio(chunks, file_name_out, original_bitrate)


    for chunk in chunks:
        os.remove(chunk)

def find_cool_moment_for_preview(filename, preview_length_ms=15000):
    audio = AudioSegment.from_file(filename)
    highest_peak = -float('inf')
    peak_time = 0

    file_info = mediainfo(filename)
    original_bitrate = file_info['bit_rate']

    chunk_length_ms = 1000
    for i in range(0, len(audio) - preview_length_ms, chunk_length_ms):
        chunk = audio[i:i + chunk_length_ms]
        chunk_rms = chunk.rms
        if chunk_rms > highest_peak:
            highest_peak = chunk_rms
            peak_time = i

    start_time = max(peak_time - (preview_length_ms // 2), 0)
    end_time = start_time + preview_length_ms
    preview_chunk = audio[start_time:end_time]

    preview_filename = f"{filename}_{int(start_time // 1000)}_{int(end_time // 1000)}.mp3"
    preview_chunk.export(preview_filename, format='mp3', bitrate=original_bitrate)

    return preview_filename

def get_preview_samples(file_name_in):
    upload_id, asset_id, etag = upload_file(find_cool_moment_for_preview(file_name_in))
    max_threads.release()
    complete_upload(upload_id, etag)
    samples = get_mastering_samples(asset_id)
    delete_asset(asset_id)
    return samples