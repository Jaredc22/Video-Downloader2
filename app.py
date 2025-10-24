import streamlit as st
from pathlib import Path
from youtube_downloader_core import download_youtube

st.set_page_config(page_title="YouTube Downloader")
st.title("🎬 YouTube Downloader")

url = st.text_input("Enter YouTube URL:")
col1, col2 = st.columns(2)
with col1:
    audio_only = st.checkbox("Audio Only", value=False, help="MP3 if ffmpeg is available; otherwise M4A/WEBM fallback.")
with col2:
    resolution = st.selectbox("Max Resolution", ["1080", "720", "480", "360"], index=0)

download_path = "./downloads"  # keep in app working dir

if st.button("Download"):
    with st.spinner("Downloading..."):
        ok, filepath, msg = download_youtube(
            url=url,
            audio_only=audio_only,
            resolution=resolution,
            download_path=download_path
        )
    if ok and filepath:
        st.success(msg)
        fp = Path(filepath)
        try:
            st.download_button(
                label=f"⬇️ Download {fp.name}",
                data=fp.read_bytes(),
                file_name=fp.name
            )
        except Exception as e:
            st.info(f"Saved to: {fp}")
            st.error(f"Could not attach file for download: {e}")
    else:
        st.error(msg)