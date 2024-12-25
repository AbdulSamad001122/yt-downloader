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
                for fmt in info.get('formats', [])
                if fmt.get('ext') == 'mp4'
            ]
            return formats
    except yt_dlp.utils.DownloadError as e:
        return f"Download error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"

# Function to download the video
def download_video(url, format_id, output_filename):
    # Save file in the app's working directory
    downloads_folder = os.path.join(os.getcwd(), f"{output_filename}.mp4")
    progress_bar = st.progress(0)

    def progress_hook(d):
        if d['status'] == 'downloading':
            if 'total_bytes' in d and d['total_bytes'] > 0:
                progress = min(max(d['downloaded_bytes'] / d['total_bytes'], 0), 1)
                progress_bar.progress(progress)
        elif d['status'] == 'finished':
            progress_bar.progress(1.0)

    try:
        opts = {
            'outtmpl': downloads_folder,
            'format': format_id,
            'progress_hooks': [progress_hook],
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        return downloads_folder
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
