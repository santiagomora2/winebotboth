import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
import os

# API key para OpenAI
OPENAI_API_KEY = st.secrets['API_KEY']
client = OpenAI(api_key=OPENAI_API_KEY)

# Función para convertir audio a texto
def audio_to_text(path):
    with open(path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )
    return transcription.text

# Función para convertir texto a audio
def text_to_audio(text):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    audio_file = "output.mp3"
    response.stream_to_file(audio_file)
    return audio_file

# Maneja la pregunta y responde utilizando IA
def handle_question(question):
    initial_prompt = (
        "Actúa como un sommelier experto en vinos, especializado en ofrecer recomendaciones personalizadas y detalladas..."
        # Se incluye el resto del prompt inicial que aparece en ambos scripts
    )

    # Construir el historial de mensajes
    messages_for_api = [{"role": "system", "content": initial_prompt}] + [
        {"role": msg['role'], "content": msg['content']} for msg in st.session_state.messages
    ]

    completion = client.chat.completions.create(
        model="ft:gpt-4o-mini-2024-07-18:tae::AFlqsMGP",
        messages=messages_for_api
    )

    return completion.choices[0].message.content

# Interfaz en streamlit
def main():
    # Configuración de fondo y estilo
    bg = '''
    <style>
    [data-testid="stAppViewContainer"]{
    background-image: url("https://img.freepik.com/premium-photo/wine-wooden-table-background-blurred-wine-shop-with-bottles_191555-1126.jpg?w=1060");
    background-size: cover;
    }
    [data-testid="stMainBlockContainer"]{
    background-color: rgba(0,0,0,.5);
    }
    [data-testid="stHeader"]{
    background-color: rgba(0,0,0,0);
    }
    [data-testid="stMarkdown"]{
    color: rgb(255,255,255);
    }
    </style>
    '''

    st.markdown(bg, unsafe_allow_html=True)
    st.title("Asistente de Vinos: Chatbot y Voz")

    # Inicializar el estado de la sesión para almacenar los mensajes si no existe
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Opciones de interacción
    option = st.selectbox("¿Cómo te gustaría interactuar?", ("Escribir", "Hablar"))

    if option == "Escribir":
        if prompt := st.chat_input("Ingresa tu pregunta:"):
            # Guardar y mostrar el mensaje del usuario
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Maneja la pregunta
            with st.spinner("Consultando la IA..."):
                response = handle_question(prompt)
                st.session_state.messages.append({"role": "assistant", "content": response})

            # Mostrar la respuesta
            with st.chat_message("assistant", avatar='🍷'):
                st.markdown(response)

    elif option == "Hablar":
        audio_bytes = audio_recorder(text="Haz click para comenzar a hablar!", recording_color="#ff0000", neutral_color="#d3d3d3")

        if audio_bytes:
            path = 'myfile.wav'
            with open(path, 'wb') as f:
                f.write(audio_bytes)

            try:
                # Transcribe el audio
                with st.spinner("Transcribiendo el audio..."):
                    try:
                        question = audio_to_text(path)
                        st.session_state.messages.append({"role": "user", "content": question})  # Agregar el mensaje del usuario al historial
                    except:
                        st.error('No se pudo escuchar tu mensaje! \n Intenta hacer click en el micrófono, hablar cuando se ponga color rojo y, cuando dejes de hablar, automáticamente se procesará tu pregunta', icon="🚨")
            finally:
                if os.path.exists(path):
                    os.remove(path)

            # Maneja la pregunta con IA
            with st.spinner("Consultando la IA..."):
                response = handle_question(question)
                st.session_state.messages.append({"role": "assistant", "content": response})

            # Convierte la respuesta a audio y lo reproduce automáticamente
            with st.spinner("Convirtiendo la respuesta a audio..."):
                audio_file = text_to_audio(response)

            st.audio(audio_file, autoplay=True)

            # Elimina el archivo temporal de audio
            if os.path.exists(audio_file):
                os.remove(audio_file)


if __name__ == "__main__":
    main()
