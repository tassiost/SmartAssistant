import asyncio      #async
import sseclient    #streaming
import sys          #streaming

import requests     #api call
import json         #api call
import base64       #encode audio

#TTS
from gtts import gTTS
from io import BytesIO

#Streamlit
import streamlit as st
import streamlit_chat

# For local streaming, the websockets are hosted without ssl - ws://
PORT = 7860                         #default port
HOST = f'localhost:{PORT}'          #HOST = 'localhost:5005'

# For reverse-proxied streaming, the remote will likely host with ssl - wss://
# URI = 'wss://your-uri-here.trycloudflare.com/api/v1/stream'

URIprefixValue = "connect-eden-beverage-strips"

st.set_page_config(
    page_title="Chat",
    page_icon="🤖",                         #👋
    initial_sidebar_state="auto",           #collapsed
    #layout='wide'
)

with st.sidebar:
    if "URIpre" not in st.session_state:
        #st.session_state.URIpre = URIprefixValue
        st.text_input(label="URI prefix", key="URIpre", value=URIprefixValue, placeholder=URIprefixValue, help="The URI prefix")    #set uri prefix from textgenUI
    else:
        st.text_input(label="URI prefix", key="URIpre", value=st.session_state.URIpre, placeholder=st.session_state.URIpre, help="The URI prefix")    #set uri prefix from textgenUI
    #st.write(st.session_state.URIpre)

    URI = f'http://{st.session_state.URIpre}.trycloudflare.com/v1/chat/completions'     #add prefix to get complete URI
    temp = st.number_input("Temperature", value=1, help="Default 1")                    #set low to get deterministic results
    #st.session_state.URIprefix = URIprefix.value

    ttsOn = st.toggle("TTS")

async def run(user_input, history, stream, regenerate, continuation):
    history.append({"role": "user", "content": user_input})

    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        'mode': 'chat',             #'mode': 'chat-instruct',        #'mode': 'instruct',
        'stream': stream,
        'messages': history,
        'character': 'Arc',
        'instruction_template': 'Orca-Hashes',                       #WizardLM
        #'your_name': st.session_state.userid,                       #doesnt work?

        'regenerate': regenerate,
        '_continue': continuation,
        #'stop_at_newline': False,
        #'chat_prompt_size': 2048,
        #'chat_generation_attempts': 1,
        #'chat-instruct_command': 'Continue the chat dialogue below. Write a single reply for the character "<|character|>".\n\n<|prompt|>',
        #'max_new_tokens': 250,
        #'do_sample': True,
        'temperature': temp,
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

    stream_response = requests.post(URI, headers=headers, json=data, verify=False, stream=True)
    if str(stream_response) != "<Response [200]>":
        st.error("Server down or not set correct URI")

    client = sseclient.SSEClient(stream_response)
    
    element = st.empty()
    assistant_message = ''
    for event in client.events():
        payload = json.loads(event.data)
        chunk = payload['choices'][0]['message']['content']
        assistant_message += chunk
        print(chunk, end='')
        sys.stdout.flush()  # If we don't flush, we won't see tokens in realtime.
        element.write(assistant_message)

    element.empty()
    history.append({"role": "assistant", "content": assistant_message})

    print()
    print("+++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(history)
    return assistant_message

#Be sure to end each prompt string with a comma.
example_user_prompts = [
    "who are you?",
    "what is your name?",
    "what is your real name?",
    "what is your purpose?",
    "echo Hello World!",
    "How old is Elon Musk?",
    "What makes a good joke?",
    "Tell me a haiku.",
    "what is the first question I asked?",
]

def move_focus():
    #Inspect the html to determine which control to specify to receive focus (e.g. text or textarea).
    st.components.v1.html(
        f"""
            <script>
                var textarea = window.parent.document.querySelectorAll("textarea[type=textarea]");
                for (var i = 0; i < textarea.length; ++i) {{
                    textarea[i].focus();
                }}
            </script>
        """,
    )

def complete_messages(nbegin,nend,stream,regenerate,continuation):
    messages = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ]
    with st.spinner(f"Waiting for {nbegin}/{nend} responses..."):
        response_content = asyncio.run(run(st.session_state.messages[-1]['content'], messages, stream, regenerate, continuation))
        print(response_content)

        #using OPENAI?
            #response = openai.ChatCompletion.create(
            #    model=st.session_state["openai_model"],
            #    messages=[
            #        {"role": m["role"], "content": m["content"]}
            #        for m in st.session_state.messages
            #    ],
            #    stream=False,
            #)
            #response_content = response.choices[0]['message'].get("content","")
            #response_content = asyncio.run(run(st.session_state.messages[-1]['content'], messages, stream, regenerate))
            #print(response_content)
    return response_content

def chat():
    #if "openai_model" not in st.session_state:
    #    st.session_state["openai_model"] = "gpt-3.5-turbo"

    if "messages" not in st.session_state:
        st.session_state.messages = []

    #if "userid" not in st.session_state:
    #    st.session_state.userid = "You"
    #else:
    #    st.sidebar.text_input("Current userid", on_change=userid_change, placeholder=st.session_state.userid, key='userid_input')
        
    #Clear conversation
    if st.sidebar.button("Clear Conversation", key='clear_chat_button'):
        st.session_state.messages = []
        move_focus()

    #Example conversation
    if st.sidebar.button("Show Example Conversation", key='show_example_conversation'):
        #st.session_state.messages = [] # don't clear current conversations?
        for i,up in enumerate(example_user_prompts):
            st.session_state.messages.append({"role": "user", "content": up})
            assistant_content = complete_messages(i,len(example_user_prompts), True, False, False)
            st.session_state.messages.append({"role": "assistant", "content": assistant_content})
        move_focus()

    #st.write(st.session_state.messages)            #debug
        
    #Regenerate & continue
    if (len(st.session_state.messages) > 0):        #only let regenerate and continue if something was already asked
        #Regenerate
        if st.sidebar.button("Regenerate", key='regenerate'):
            st.session_state.messages.pop()         #remove last answer to regenerate
            assistant_content = complete_messages(0,1, True, True, False)
            st.session_state.messages.append({"role": "assistant", "content": assistant_content})
            if (ttsOn): TTS(assistant_content)
            move_focus()
            
        #Continue
        if st.sidebar.button("Continue", key='continue'):
            st.session_state.messages.pop()         #TODO: instead of regenerating try not to pop but adjust the key
            assistant_content = complete_messages(0,1, True, False, True)
            st.session_state.messages.append({"role": "assistant", "content": assistant_content})
            if (ttsOn): TTS(assistant_content)
            move_focus()

    #Assign keys to chat messages
    for i,message in enumerate(st.session_state.messages):
        nkey = int(i/2)
        if message["role"] == "user":
            streamlit_chat.message(message["content"], is_user=True, key='chat_messages_user_'+str(nkey))
        else:
            streamlit_chat.message(message["content"], is_user=False, key='chat_messages_assistant_'+str(nkey))

    #Chat input
    if user_content := st.chat_input("Start typing..."): # using streamlit's st.chat_input because it stays put at bottom, chat.openai.com style.
        nkey = int(len(st.session_state.messages)/2)
        st.session_state.messages.append({"role": "user", "content": user_content})
        streamlit_chat.message(user_content, is_user=True, key='chat_messages_user_'+str(nkey))
        
        assistant_content = complete_messages(0,1, True, False, False)
        st.session_state.messages.append({"role": "assistant", "content": assistant_content})
        streamlit_chat.message(assistant_content, key='chat_messages_assistant_'+str(nkey))

        if (ttsOn): TTS(assistant_content)
        
        #debug
        print("-------------------------Messages---------------------")
        print(st.session_state.messages)
        #len(st.session_state.messages)
    #else:
    #    st.sidebar.text_input(
    #        "Enter a random userid", on_change=userid_change, placeholder='userid', key='userid_input')
    #    streamlit_chat.message("Hi. I'm your friendly streamlit ChatGPT assistant.",key='intro_message_1')
    #    streamlit_chat.message("To get started, enter a random userid in the left sidebar.",key='intro_message_2')

@st.cache_data()
def TTS(txt):
    sound_file = BytesIO()
    tts = gTTS(str(txt), lang='en')
    tts.write_to_fp(sound_file)
    tts.save('temp.mp3')

    # Read the audio file and encode it to base64
    with open('temp.mp3', "rb") as audio_file:
        audio_bytes = base64.b64encode(audio_file.read()).decode()

    # Use HTML to embed audio with autoplay
    st.markdown(
        f'<audio autoplay="true" controls style="width:100%;">><source src="data:audio/mp3;base64,{audio_bytes}" type="audio/mp3"></audio>',
        unsafe_allow_html=True,
    )

    #audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')                               #expects audio?
    #audio_tag = f'<audio autoplay="true" src="data:audio/wav;base64,{audio_base64}">'
    #st.markdown(audio_tag, unsafe_allow_html=True)

    #st.audio(sound_file, autoplay=True)                                                        #autoplay doesnt seem to work

def userid_change():
    st.session_state.userid = st.session_state.userid_input

def main():
    chat()

if __name__ == '__main__':
    main()    