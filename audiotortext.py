import streamlit as st
from faster_whisper import WhisperModel
import ollama
import os

# Initialize Ollama client
client = ollama.Client('http://localhost:11434')

# Streamlit UI
st.title("🎙️ Audio Transcription & Summarization App")

# File uploader for audio files
uploaded_file = st.file_uploader("Upload an audio file", type=["wav", "mp3", "m4a"])

if uploaded_file:
    # Save the uploaded file temporarily
    file_path = os.path.join("temp_audio", uploaded_file.name)
    os.makedirs("temp_audio", exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.success(f"File '{uploaded_file.name}' uploaded successfully!")

    # Step 1: Transcribe the audio file
    with st.spinner("Transcribing audio..."):
        model = WhisperModel("base.en", device="cpu")
        segments, _ = model.transcribe(file_path)
        transcript = " ".join(segment.text for segment in segments)
    st.text_area("📝 Transcription", transcript, height=300)

    # Step 2: Summarize the transcription using Ollama
    with st.spinner("Summarizing transcription..."):
        response = client.chat(model='mistral', messages=[
            {"role": "user", "content": f"Summarize this meeting transcription:\n\n{transcript}"}
        ])
        summary = response.get('message', {}).get('content', 'Failed to summarize.')
    st.success("✅ Summary Generated!")
    st.text_area("📄 Meeting Summary", summary, height=200)

    # Cleanup
    os.remove(file_path)
