import streamlit as st
import yt_dlp
import os
import subprocess
import requests
import shutil

# Function to download FFmpeg
def download_ffmpeg():
    ffmpeg_url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n7.1-latest-win64-lgpl-7.1.zip"
    ffmpeg_zip = "ffmpeg.zip"
    ffmpeg_extract_dir = "ffmpeg"
    ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg.exe")

    # Download the FFmpeg zip file if it doesn't already exist
    if not os.path.exists(ffmpeg_zip):
        response = requests.get(ffmpeg_url, stream=True)
        with open(ffmpeg_zip, "wb") as f:
            shutil.copyfileobj(response.raw, f)

    # Extract the FFmpeg zip file if the folder doesn't exist
    if not os.path.exists(ffmpeg_extract_dir):
        shutil.unpack_archive(ffmpeg_zip, ffmpeg_extract_dir)

    # Search for ffmpeg.exe within the extracted folder
    ffmpeg_extracted_path = None
    for root, dirs, files in os.walk(ffmpeg_extract_dir):
        if "ffmpeg.exe" in files:
            ffmpeg_extracted_path = os.path.join(root, "ffmpeg.exe")
            break

    if not ffmpeg_extracted_path:
        raise FileNotFoundError("FFmpeg executable not found in the extracted files.")

    # Move the FFmpeg executable to the working directory if it doesn't already exist
    if not os.path.exists(ffmpeg_path):
        shutil.move(ffmpeg_extracted_path, ffmpeg_path)

    return ffmpeg_path

# Function to list available formats
def list_formats(url):
    try:
        opts = {'listformats': True}
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = [
                {
                    "id": fmt['format_id'],
                    "resolution": f"{fmt.get('height', 'Unknown')}p" if 'height' in fmt else "Audio Only",
                    "fps": fmt.get('fps', "N/A"),
                    "filesize": fmt.get('filesize', "Unknown"),
                    "ext": fmt['ext']
                }
                for fmt in info.get('formats', [])
            ]
            return formats
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Function to download and merge video and audio
def download_video(url, format_id, output_filename, ffmpeg_path):
    video_file = f"{output_filename}_video.mp4"
    audio_file = f"{output_filename}_audio.mp4"
    output_file = f"{output_filename}.mp4"
    progress_bar = st.progress(0)

    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes', 1)
            downloaded = d.get('downloaded_bytes', 0)
            progress = downloaded / total if total > 0 else 0
            progress = max(0.0, min(1.0, progress))
            progress_bar.progress(progress)
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)

    try:
        # Download video
        opts_video = {'format': format_id, 'outtmpl': video_file, 'progress_hooks': [progress_hook]}
        with yt_dlp.YoutubeDL(opts_video) as ydl:
            ydl.download([url])

        # Download audio
        opts_audio = {'format': 'bestaudio/best', 'outtmpl': audio_file, 'progress_hooks': [progress_hook]}
        with yt_dlp.YoutubeDL(opts_audio) as ydl:
            ydl.download([url])

        # Merge video and audio
        ffmpeg_command = [
            ffmpeg_path,
            "-i", video_file,
            "-i", audio_file,
            "-c:v", "copy",
            "-c:a", "aac",
            "-strict", "experimental",
            output_file
        ]
        subprocess.run(ffmpeg_command, check=True)

        # Cleanup
        os.remove(video_file)
        os.remove(audio_file)

        return output_file
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Streamlit app
st.title("YouTube Video Downloader")

url = st.text_input("Enter the YouTube URL")
if url:
    st.write("Fetching video formats...")
    formats = list_formats(url)

    if isinstance(formats, str):
        st.error(formats)
    elif formats:
        st.write("Available formats:")
        for fmt in formats:
            st.write(f"ID: {fmt['id']} | Resolution: {fmt['resolution']} | FPS: {fmt['fps']} | Filesize: {fmt['filesize']} | Extension: {fmt['ext']}")

        format_id = st.text_input("Enter the Format ID to download")
        output_filename = st.text_input("Enter the desired output filename (without extension)")

        if st.button("Download"):
            if format_id and output_filename:
                ffmpeg_path = download_ffmpeg()
                result = download_video(url, format_id, output_filename, ffmpeg_path)
                if os.path.exists(result):
                    st.success("Download completed successfully! Use the button below to save your file.")
                    with open(result, "rb") as file:
                        st.download_button(
                            label="Download Video",
                            data=file,
                            file_name=f"{output_filename}.mp4",
                            mime="video/mp4"
                        )
                else:
                    st.error(f"An error occurred: {result}")
            else:
                st.error("Please enter both a valid Format ID and a filename.")
    else:
        st.warning("No formats found. Please check the URL or try another video.")
