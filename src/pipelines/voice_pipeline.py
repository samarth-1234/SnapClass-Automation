from resemblyzer import VoiceEncoder, preprocess_wav
import numpy as np
import io       #Allows reading audio bytes directly from memory
import librosa      #Loads and processes audio files
import streamlit as st


@st.cache_resource
def load_voice_encoder():
    return VoiceEncoder()       #voice into a 256-dimensional embedding.

def get_voice_embedding(audio_bytes):
    try:
        encoder = load_voice_encoder()

        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)         #Read audio
        wav = preprocess_wav(audio)         #Cleans and prepares audio
        embedding = encoder.embed_utterance(wav)        #256 Dimension Vector
        return embedding.tolist()

    except Exception as e:
        st.error("Voice Recog Error!")
        return None

def identify_speaker(new_embedding, candidates_dict, threshold=0.65):       #Compare one unknown voice with all stored voices.
    if new_embedding is None or not candidates_dict:
        return None, 0.0

    best_sid = None
    best_score = -1.0

    for sid, store_embedding in candidates_dict.items():
        if store_embedding:
            similarity = np.dot(new_embedding, store_embedding) / (
                np.linalg.norm(new_embedding) *
                np.linalg.norm(store_embedding)
            )
            if similarity > best_score:
                best_score = similarity
                best_sid = sid


    if best_score >= threshold:
        return best_sid, best_score

    return None, best_score

def process_bulk_audio(audio_bytes, candidates_dict, threshold = 0.65):        #Process a long recording containing several speaking sections
    try:
        encoder = load_voice_encoder()
        
        audio, sr = librosa.load(io.BytesIO(audio_bytes), sr=16000)

        segments = librosa.effects.split(audio, top_db=30)

        identified_results = {}

        for start, end in segments:
            if (end-start) < sr * 0.5:
                continue
            segment_audio = audio[start:end]
            wav = preprocess_wav(segment_audio)
            embedding = encoder.embed_utterance(wav)

            sid, score = identify_speaker(embedding, candidates_dict, threshold)

            if sid:
                if sid not in identified_results or score > identified_results[sid]:
                    identified_results[sid] = score

        return identified_results

    except Exception as e:
        st.error("Bulk Process Error!")
        return {}