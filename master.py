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

def master_chunk(chunk):
    max_threads.acquire()
    try:        
        upload_id, asset_id, etag = upload_file(chunk)
        max_threads.release()
        complete_upload(upload_id, etag)
        samples = get_mastering_samples(asset_id)
        for sample in samples:
            if sample['intensity'] == 'Medium' and sample['style'] == 'PS2':
                content = requests.get(sample['mp3Url']).content
                with open(chunk, 'wb') as f:
                    f.write(content)
        delete_asset(asset_id)
    finally:
        pass

def master_track(file_name_in, file_name_out):
    file_info = mediainfo(file_name_in)
    original_bitrate = file_info['bit_rate']

    chunks = split_audio(file_name_in)

    threads = []

    for chunk in chunks:
        thread = threading.Thread(target=master_chunk, args=(chunk,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    merge_audio(chunks, file_name_out, original_bitrate)


    for chunk in chunks:
        os.remove(chunk)