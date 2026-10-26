# In Tab 1 (AI Intelligence Hub)
audio_file = st.audio_input("🎙️ Speak your question (Voice-to-Text)")

if audio_file is not None:
    # 1. Read the recorded audio bytes
    audio_bytes = audio_file.read()
    
    # 2. Pass the audio bytes directly into Gemini alongside your documents!
    # Gemini 2.5 Flash natively understands audio inputs.
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav"),
            "Listen to this audio question regarding our union contract/policies and provide a precise answer."
        ]
    )
    st.markdown("### VOICE QUERY OUTPUT:")
    st.markdown(f"<div class='tech-card'>{response.text}</div>", unsafe_allow_html=True)
