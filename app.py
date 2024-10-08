# Command to run the app
# python -m streamlit run app.py

import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

from gtts import gTTS
from io import BytesIO
import openai

# added for circular image
from PIL import Image, ImageDraw

openai.api_key = "your-api-key"

if 'prompts' not in st.session_state:
    st.session_state['prompts'] = [{"role": "system",
                                    "content": "You are a helpful assistant. Answer as concisely as possible with a little humor expression."}]


def generate_response(prompt):
    st.session_state['prompts'].append({"role": "user", "content": prompt})
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=st.session_state['prompts']
    )

    message = completion.choices[0].message.content
    return message

# added for circular image
def generate_circular_radius(image_file):
    # Open the image using Pillow library
    image = Image.open(image_file)

    # Define the radius of the circular image
    radius = min(image.size) / 2

    # Create a circular mask
    mask = Image.new("L", image.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, image.size[0], image.size[1]), fill=255)

    # Apply the mask to the image
    image.putalpha(mask)
    return image


sound = BytesIO()

placeholder = st.container()

placeholder.title("AI VoiceBot")
stt_button = Button(label='SPEAK', button_type='success', margin=(5, 5, 5, 5), width=200)

stt_button.js_on_event("button_click", CustomJS(code="""
    var value = "";
    var rand = 0;
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en';

    document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'start'}));

    recognition.onspeechstart = function () {
        document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'running'}));
    }
    recognition.onsoundend = function () {
        document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'stop'}));
    }
    recognition.onresult = function (e) {
        var value2 = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
                rand = Math.random();

            } else {
                value2 += e.results[i][0].transcript;
            }
        }
        document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: {t:value, s:rand}}));
        document.dispatchEvent(new CustomEvent("GET_INTRM", {detail: value2}));

    }
    recognition.onerror = function(e) {
        document.dispatchEvent(new CustomEvent("GET_ONREC", {detail: 'stop'}));
    }
    recognition.start();
    """))

result = streamlit_bokeh_events(
    bokeh_plot=stt_button,
    events="GET_TEXT,GET_ONREC,GET_INTRM",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

tr = st.empty()

if 'input' not in st.session_state:
    st.session_state['input'] = dict(text='', session=0)

tr.text_area("**Your input**", value=st.session_state['input']['text'])

if result:
    if "GET_TEXT" in result:
        if result.get("GET_TEXT")["t"] != '' and result.get("GET_TEXT")["s"] != st.session_state['input']['session']:
            st.session_state['input']['text'] = result.get("GET_TEXT")["t"]
            tr.text_area("**Your input**", value=st.session_state['input']['text'])
            st.session_state['input']['session'] = result.get("GET_TEXT")["s"]

    if "GET_INTRM" in result:
        if result.get("GET_INTRM") != '':
            tr.text_area("**Your input**", value=st.session_state['input']['text'] + ' ' + result.get("GET_INTRM"))

    if "GET_ONREC" in result:
        if result.get("GET_ONREC") == 'start':
            # Display the circular image using Streamlit
            placeholder.image("mic.gif")
            # placeholder.image(generate_circular_radius("recon.jpg"), caption="Circular Image", use_column_width=True)
            st.session_state['input']['text'] = ''
        elif result.get("GET_ONREC") == 'running':
            placeholder.image("mic.gif")
            # placeholder.image(generate_circular_radius("recon.jpg"), caption="Circular Image", use_column_width=True)
        elif result.get("GET_ONREC") == 'stop':
            placeholder.image("mic.jpg")
            # placeholder.image(generate_circular_radius("recon.jpg"), caption="Circular Image", use_column_width=True)
            if st.session_state['input']['text'] != '':
                input = st.session_state['input']['text']
                output = generate_response(input)
                st.write("**ChatBot:**")
                st.write(output)
                st.session_state['input']['text'] = ''

                tts = gTTS(output, lang='en', tld='com')
                tts.write_to_fp(sound)
                st.audio(sound)

                st.session_state['prompts'].append({"role": "user", "content": input})
                st.session_state['prompts'].append({"role": "assistant", "content": output})
