import time         #timer
import asyncio      #async
import sseclient    #streaming

import requests     #api call
import json         #api call
import base64       #encode audio

#Streamlit
import streamlit as st
import streamlit_chat

#TTS
from gtts import gTTS
from io import BytesIO

#STT
from streamlit_mic_recorder import speech_to_text

#IMPORTANT URI prefix (found in Oobabooga terminal)
URIprefixValue = "friendship-origins-antarctica-spirituality"

#Make sure to end each prompt string with a comma.
exampleUserPrompts = [
    "who are you?",
    "what is your name?",
    "what is your real name?",
    "what is your purpose?",
    "echo Hello World!",
    "what color is the sun?",
    "how old is Elon Musk?",
    "what makes a good joke?",
    "tell me a haiku.",
    "what was the first question I asked?",
]

st.set_page_config(
    page_title="Smart Assistant",
    page_icon="🤖",
    initial_sidebar_state="auto", #collapsed
    #layout='wide'
)

with st.sidebar:
    st.subheader("Server")
    #URI prefix
    if "URIpre" not in st.session_state:
        st.text_input(label="URI prefix", key="URIpre", value=URIprefixValue, placeholder=URIprefixValue, help="The URI prefix. Ask Tassio Steinmann for access.") #set uri prefix from Oobabooga
    else:
        st.text_input(label="URI prefix", key="URIpre", value=st.session_state.URIpre, placeholder=st.session_state.URIpre, help="The URI prefix. Ask Tassio Steinmann for access.")

    URI = f'http://{st.session_state.URIpre}.trycloudflare.com/v1/chat/completions' #add prefix to get complete URI

    #Parameters
    temperature = st.slider("Temperature", value=0.7, min_value=0.05, max_value=1.5, help="Default 0.7. Higher values lead to more variation, randomness and creativity.")

    #st.divider()

    st.subheader("Client")
    #Toggles
    ttsOn = st.toggle("Text to Speech", value=True, help="Toggle Text to Speech")
    historyOn = st.toggle("History", value=True, help="Toggle History. When enabled use the Clear Conversation button to wipe the memory")

async def run(user_input, history, stream, regenerate, continuation):
    history.append({"role": "user", "content": user_input})

    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        'mode': 'chat', #'mode': 'chat-instruct', #'mode': 'instruct',
        'stream': stream,
        'messages': history,
        'character': 'Arc 2',
        'instruction_template': 'Orca-Hashes', #WizardLM
        'your_name': 'Tassio Steinmann', #doesnt work?

        'regenerate': regenerate,
        '_continue': continuation,
        #'stop_at_newline': False,
        #'chat_prompt_size': 2048,
        #'chat_generation_attempts': 1,
        #'chat-instruct_command': 'Continue the chat dialogue below. Write a single reply for the character "<|character|>".\n\n<|prompt|>',
        #'max_new_tokens': 250,
        #'do_sample': True,
        'temperature': temperature,
        #'top_p': 0.1,
        #'typical_p': 1,
        #'epsilon_cutoff': 0,  # In units of 1e-4
        #'eta_cutoff': 0,  # In units of 1e-4
        #'tfs': 1,
        #'top_a': 0,
        #'repetition_penalty': 1.18,
        #'top_k': 40,
        #'min_length': 0,
        #'no_repeat_ngram_size': 0,
        #'num_beams': 1,
        #'penalty_alpha': 0,
        #'length_penalty': 1,
        #'early_stopping': False,
        #'mirostat_mode': 0,
        #'mirostat_tau': 5,
        #'mirostat_eta': 0.1,
        #'seed': 1,
        #'add_bos_token': True,
        #'truncation_length': 2048,
        #'ban_eos_token': False,
        #'skip_special_tokens': True,
        #'stopping_strings': []
    }

    streamResponse = requests.post(URI, headers=headers, json=data, verify=False, stream=True)
    if str(streamResponse) != "<Response [200]>":
        st.error("Server down or not set correct URI prefix in sidebar")

    #Streaming text
    client = sseclient.SSEClient(streamResponse)
    element = st.empty()                    
    assistantMessage = ''
    for event in client.events(): #try using st.write_stream
        payload = json.loads(event.data)
        chunk = payload['choices'][0]['message']['content']
        assistantMessage += chunk
        element.write(assistantMessage)
    element.empty() #remove streamed text to replace with text message                         

    return assistantMessage

def moveFocus():
    st.components.v1.html(
        f"""
            <script>
                var textarea = window.parent.document.querySelectorAll("textarea[type=textarea]");
                for (var i = 0; i < textarea.length; ++i) {{
                    textarea[i].focus();
                }}
            </script>
        """,
        height = 0,
    )

def completeMessages(nbegin, nend, stream, regenerate, continuation):
    messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
    with st.spinner(f"Waiting for {nbegin}/{nend} responses..."):
        responseContent = asyncio.run(run(st.session_state.messages[-1]['content'], messages, stream, regenerate, continuation))
    return responseContent

def chat():
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    #Clear conversation
    if st.sidebar.button("Clear Conversation", key='clear_chat_button', help="Wipe memory"):
        st.session_state.messages = []
        moveFocus()

    #Chat input
    if userContent := st.chat_input("Start typing..."): #using streamlit's st.chat_input because it stays put at bottom
        chatInteraction(userContent, False)

    #Example conversation
    if st.sidebar.button("Show Example Conversation", key='show_example_conversation'):
        st.session_state.messages = [] #clear current conversations?
        for i, up in enumerate(exampleUserPrompts):
            st.session_state.messages.append({"role": "user", "content": up})
            assistantContent = completeMessages(i, len(exampleUserPrompts), True, False, False)
            st.session_state.messages.append({"role": "assistant", "content": assistantContent})
        st.session_state.messages.pop()
        chatInteraction(st.session_state.messages, True)
        moveFocus()
        
    #Regenerate & Continue
    if (len(st.session_state.messages) > 0): #only let regenerate and continue if something was already asked
        #Regenerate
        if st.sidebar.button("Regenerate", key='regenerate'):
            lastAnswer = st.session_state.messages[-1]
            st.session_state.messages.pop()
            chatInteraction(lastAnswer, True)
            moveFocus()
            
        #Continue
        if st.sidebar.button("Continue", key='continue'):
            chatInteraction("Continue", False)
            moveFocus()

@st.cache_data()
def TTS(txt):
    startTime = time.time() #Start timer

    soundFile = BytesIO()
    tts = gTTS(str(txt), lang='en')
    tts.write_to_fp(soundFile)
    tts.save('temp.mp3')

    #Read the audio file and encode it to base64
    with open('temp.mp3', "rb") as audioFile:
        audioBytes = base64.b64encode(audioFile.read()).decode()

    #st.audio(soundFile, autoplay=True) #autoplay doesn't work yet
    st.markdown( #Use HTML to embed audio with autoplay
        f'<audio autoplay="true" controls style="width:100%;">><source src="data:audio/mp3;base64,{audioBytes}" type="audio/mp3"></audio>',
        unsafe_allow_html=True,
    )    

    stopTimer(startTime, "TTS") #Stop timer

def chatInteraction(input, skipUser):
    startTime = time.time() #Start timer

    #Assign keys to chat messages
    for i, message in enumerate(st.session_state.messages):
        nkey = int(i/2)
        if message["role"] == "user":
            streamlit_chat.message(message["content"], is_user=True, key='chat_messages_user_' + str(nkey))
        else:
            streamlit_chat.message(message["content"], is_user=False, key='chat_messages_assistant_' + str(nkey))
    nkey = int(len(st.session_state.messages) / 2 + 1)

    if (not skipUser):
        st.session_state.messages.append({"role": "user", "content": input})
        streamlit_chat.message(input, is_user=True, key='chat_messages_user_' + str(nkey))
    
    assistantContent = completeMessages(0, 1, True, False, False)
    while (assistantContent == ''): #Regenerate if answer is empty
        assistantContent = completeMessages(0, 1, True, True, False)
    st.session_state.messages.append({"role": "assistant", "content": assistantContent})
    streamlit_chat.message(assistantContent, key='chat_messages_assistant_' + str(nkey))
    
    stopTimer(startTime, "LLM") #Stop timer

    if (ttsOn): TTS(assistantContent)

    if not historyOn:
        st.session_state.messages = []

def stopTimer(startTime, string):
    endTime = time.time()
    timeLapsed = endTime - startTime
    roundedNumber = format(timeLapsed, ".2f")
    st.write(string + " response time: " + str(roundedNumber) + " seconds")

def callback():    
    if st.session_state.my_stt_output:
        chatInteraction(st.session_state.my_stt_output, False)
        moveFocus()

def main():
    chat()

    speech_to_text(
        language='en',
        start_prompt="Start recording",
        stop_prompt="Stop recording",
        just_once=True,
        use_container_width=True,
        args=(),
        kwargs={},
        key='my_stt', 
        callback=callback)

if __name__ == '__main__':
    main()
