import streamlit as st
import yt_dlp
import os
import subprocess

# Function to list available formats
def list_formats(url):
    try:
        opts = {
            'ffmpeg_location': r"C:\Users\Abdul Samad\Desktop\Abdul Samad\Projects\yt-downloader\ffmpeg\ffmpeg-n7.1-latest-win64-lgpl-7.1\bin\ffmpeg.exe",  # Specify your ffmpeg path here
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
                if fmt.get('ext') == 'mp4'
            ]
            return formats
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Function to download and merge video and audio
def download_video(url, format_id, output_filename):
    # Save file in the app's working directory
    downloads_folder_video = os.path.join(os.getcwd(), f"{output_filename}_video.mp4")
    downloads_folder_audio = os.path.join(os.getcwd(), f"{output_filename}_audio.mp4")
    progress_bar = st.progress(0)

    def progress_hook(d):
        # Ensuring the progress value is between 0.0 and 1.0
        if d['status'] == 'downloading':
            total = d.get('total_bytes', 1)
            downloaded = d.get('downloaded_bytes', 0)
            progress = downloaded / total if total > 0 else 0
            progress = max(0.0, min(1.0, progress))  # Ensure it's within 0.0 to 1.0
            progress_bar.progress(progress)
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)

    try:
        # Download Video
        opts_video = {
            'ffmpeg_location': r"C:\Users\Abdul Samad\Desktop\Abdul Samad\Projects\yt-downloader\ffmpeg\ffmpeg-n7.1-latest-win64-lgpl-7.1\bin\ffmpeg.exe",  # Specify your ffmpeg path here
            'outtmpl': downloads_folder_video,
            'format': f"{format_id}",
            'progress_hooks': [progress_hook],
        }

        # Download Audio
        opts_audio = {
            'ffmpeg_location': r"C:\Users\Abdul Samad\Desktop\Abdul Samad\Projects\yt-downloader\ffmpeg\ffmpeg-n7.1-latest-win64-lgpl-7.1\bin\ffmpeg.exe",  # Specify your ffmpeg path here
            'outtmpl': downloads_folder_audio,
            'format': 'bestaudio/best',
            'progress_hooks': [progress_hook],
        }

        # Download video and audio separately
        with yt_dlp.YoutubeDL(opts_video) as ydl_video:
            ydl_video.download([url])

        with yt_dlp.YoutubeDL(opts_audio) as ydl_audio:
            ydl_audio.download([url])

        # Merge the video and audio using ffmpeg
        output_file = os.path.join(os.getcwd(), f"{output_filename}.mp4")
        ffmpeg_command = [
            opts_video["ffmpeg_location"],
            "-i", downloads_folder_video,
            "-i", downloads_folder_audio,
            "-c:v", "copy", 
            "-c:a", "aac",
            "-strict", "experimental",
            output_file
        ]
        
        # Run the ffmpeg command and capture the output and error
        process = subprocess.Popen(ffmpeg_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Check for errors in ffmpeg output
        if process.returncode != 0:
            error_message = stderr.decode()
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
    st.write("Fetching video formats...")
    formats = list_formats(url)

    if isinstance(formats, str):  # Handle errors
        st.error(formats)
    elif formats:  # Display available formats if fetched successfully
        st.write("Available formats:")
        for fmt in formats:
            st.write(
                f"ID: {fmt['id']} | Resolution: {fmt['resolution']} | FPS: {fmt['fps']} | Filesize: {fmt['filesize']} | Extension: {fmt['ext']}"
            )

        # Input fields for format and filename
        format_id = st.text_input("Enter the Format ID to download")
        output_filename = st.text_input("Enter the desired output filename (without extension)")

        if st.button("Download"):
            if format_id and output_filename:
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
                st.error("Please enter both a valid Format ID and a filename.")
    else:
        st.warning("No formats found. Please check the URL or try another video.")
