import streamlit as st
import yt_dlp
import os

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
                for fmt in info['formats']
                if fmt['ext'] == 'mp4'
            ]
            return formats
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Function to download the video with progress tracking
def download_video(url, format_id, output_filename):
    # Set the path for the Downloads folder with the custom filename
    downloads_folder = os.path.expanduser(f'~\\Downloads\\{output_filename}.mp4')  # Windows
    # For Mac/Linux, use: downloads_folder = os.path.expanduser(f'~/Downloads/{output_filename}.mp4')
    
    # Create a Streamlit progress bar
    progress_bar = st.progress(0)
    
    def progress_hook(d):
        # Check if 'total_bytes' is available, otherwise handle it gracefully
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes'] > 0:
                # Ensure the progress is between 0 and 1
                progress = min(max(d['downloaded_bytes'] / d['total_bytes'], 0), 1)
                progress_bar.progress(progress)
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)  # Mark progress as complete
    
    try:
        opts = {
            'outtmpl': downloads_folder,  # Save video to Downloads folder with custom filename
            'format': format_id,          # Download the specified format ID
            'progress_hooks': [progress_hook],  # Hook to track download progress
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return f"Download completed successfully! File saved as {output_filename}.mp4"
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Streamlit application
st.title("YouTube Video Downloader")

# Input URL
url = st.text_input("Enter the YouTube URL")

if url:
    st.write("Fetching video formats...")
    formats = list_formats(url)

    # Check if formats were fetched successfully
    if isinstance(formats, str):  # Error message returned
        st.error(formats)
    else:
        # Display available formats
        st.write("Available formats:")
        for fmt in formats:
            st.write(f"ID: {fmt['id']} | Resolution: {fmt['resolution']} | FPS: {fmt['fps']} | Filesize: {fmt['filesize']}")

        # Select format
        format_id = st.text_input("Enter the Format ID to download")

        # Ask for custom output filename
        output_filename = st.text_input("Enter the desired output filename (without extension)")

        if st.button("Download"):
            if format_id and output_filename:
                result = download_video(url, format_id, output_filename)
                if "successfully" in result.lower():
                    st.success(result)
                else:
                    st.error(result)
            else:
                st.error("Please enter a valid Format ID and output filename.")
