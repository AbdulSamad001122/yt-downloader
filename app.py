import streamlit as st
import yt_dlp
import os
import subprocess
import shutil

# Use the local FFmpeg path
FFMPEG_PATH = r"E:\Projects\yt-downloader\ffmpeg\bin\ffmpeg.exe"

# Function to check if FFmpeg is present and return its path
def find_ffmpeg():
    if os.path.exists(FFMPEG_PATH):
        st.write(f"FFmpeg found at: {FFMPEG_PATH}")
        return FFMPEG_PATH
    else:
        ffmpeg_in_path = shutil.which("ffmpeg")
        if ffmpeg_in_path:
            st.write(f"FFmpeg found in system PATH at: {ffmpeg_in_path}")
            return ffmpeg_in_path
        else:
            st.error("FFmpeg not found in the specified directory or system PATH.")
            return None

# Function to list available formats
def list_formats(url):
    try:
        opts = {
            'ffmpeg_location': find_ffmpeg(),  # Specify FFmpeg path
            'listformats': True
        }
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
                if fmt.get('ext') == 'mp4'  # Only mp4 formats
            ]
            return formats
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Function to download and merge video and audio
def download_video(url, format_id, output_filename):
    downloads_folder_video = os.path.join(os.getcwd(), f"{output_filename}_video.mp4")
    downloads_folder_audio = os.path.join(os.getcwd(), f"{output_filename}_audio.mp4")
    progress_bar = st.progress(0)

    def progress_hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes', 1)
            downloaded = d.get('downloaded_bytes', 0)
            progress = downloaded / total if total > 0 else 0
            progress = max(0.0, min(1.0, progress))  # Ensure it's within 0.0 to 1.0
            progress = round(progress * 100)  # Convert to percentage
            progress_bar.progress(progress)
        elif d['status'] == 'finished':
            progress_bar.progress(100)

    try:
        # Download Video
        opts_video = {
            'ffmpeg_location': find_ffmpeg(),  # Specify FFmpeg path
            'outtmpl': downloads_folder_video,
            'format': f"{format_id}",
            'progress_hooks': [progress_hook],
        }

        # Download Audio
        opts_audio = {
            'ffmpeg_location': find_ffmpeg(),  # Specify FFmpeg path
            'outtmpl': downloads_folder_audio,
            'format': 'bestaudio/best',
            'progress_hooks': [progress_hook],
        }

        st.write("Downloading video...")
        with yt_dlp.YoutubeDL(opts_video) as ydl_video:
            ydl_video.download([url])

        st.write("Downloading audio...")
        with yt_dlp.YoutubeDL(opts_audio) as ydl_audio:
            ydl_audio.download([url])

        # Merge the video and audio using ffmpeg
        output_file = os.path.join(os.getcwd(), f"{output_filename}.mp4")
        ffmpeg_command = [
            find_ffmpeg(),
            "-i", downloads_folder_video,
            "-i", downloads_folder_audio,
            "-c:v", "copy", 
            "-c:a", "aac",
            "-strict", "experimental",
            output_file
        ]
        
        st.write("Merging video and audio...")
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            error_message = stderr.decode()
            st.error(f"FFmpeg Error: {error_message}")
            return f"FFmpeg Error: {error_message}"

        # Cleanup temporary video and audio files
        os.remove(downloads_folder_video)
        os.remove(downloads_folder_audio)

        return output_file
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Streamlit app
st.title("YouTube Video Downloader")

url = st.text_input("Enter the YouTube URL")

if url:
    st.write("Fetching video formats, please wait...")
    formats = list_formats(url)

    if isinstance(formats, str):  # Handle errors
        st.error(formats)
    elif formats:  # Display available formats if fetched successfully
        st.write("Available formats:")
        
        # Create a button for each format to select it with a unique key
        for fmt in formats:
            format_key = f"download_button_{fmt['id']}"  # Unique key based on format ID
            if st.button(f"Download {fmt['resolution']} ({fmt['fps']} FPS)", key=format_key):
                st.session_state.selected_format = fmt
                st.write(f"Selected Format: {fmt['resolution']} ({fmt['fps']} FPS)")

        # Input fields for output filename
        output_filename = st.text_input("Enter the desired output filename (without extension)")

        # Check if the format is selected before allowing download
        if 'selected_format' in st.session_state and st.session_state.selected_format:
            selected_format = st.session_state.selected_format
            st.write(f"Selected Format: {selected_format['resolution']} ({selected_format['fps']} FPS)")

            if st.button("Download") and output_filename:
                format_id = selected_format['id']
                result = download_video(url, format_id, output_filename)
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
            st.warning("Please select a format before downloading.")
    else:
        st.warning("No formats found. Please check the URL or try another video.")
