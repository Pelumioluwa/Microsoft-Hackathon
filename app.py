import asyncio
import websockets
import base64
import requests
from pydub import AudioSegment
import os

GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

# WebSocket server to receive audio from Twilio
async def twilio_websocket_handler(websocket, path):
    audio_buffer = AudioSegment.empty()
    
    async for message in websocket:
        # Decode the base64 audio data from Twilio
        audio_data = base64.b64decode(message)
        
        # Append to our audio buffer
        audio_chunk = AudioSegment(
            data=audio_data,
            sample_width=2,
            frame_rate=8000,
            channels=1
        )
        audio_buffer += audio_chunk
        
        # If we have enough audio (e.g., 5 seconds), process it
        if len(audio_buffer) >= 5000:  # 5000 ms = 5 seconds
            await process_audio(audio_buffer)
            audio_buffer = AudioSegment.empty()

async def process_audio(audio):
    # Convert audio to the format expected by Whisper
    audio_file = audio.export(format="wav")
    
    # Send to Whisper on Groq
    response = requests.post(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}"
        },
        files={"file": audio_file},
        data={"model": "whisper-1"}
    )
    
    transcription = response.json()['text']
    print(f"Transcription: {transcription}")
    # Here you would send this transcription to your generative AI

# Start the WebSocket server
async def main():
    server = await websockets.serve(
        twilio_websocket_handler, 
        "0.0.0.0", 
        int(os.environ.get("PORT", 10000))
    )
    await server.wait_closed()

if __name__ == "__main__":
    asyncio.run(main())