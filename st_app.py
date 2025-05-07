"""st_app.py
The AI Lights Changer App! Use AI to describe how you want the sign to light up
and it'll use AI to parse executable code that is sent to the sign to light it up.

To make this all work, this app uses:
-Streamlit for the web framework and cloud deployment: https://streamlit.io/
-Streamlit Authenticator for authentication: https://github.com/mkhorasani/Streamlit-Authenticator
-OpenAI API for LLM access: https://platform.openai.com/docs/overview
-Paho MQTT client library for connecting to MQTT pub/sub broker: https://pypi.org/project/paho-mqtt/
-EMQX for the MQTT pub/sub broker: https://www.emqx.com/en

Note: the lights in the sign are controlled by an ESP32 running CircuitPlayground and the
Adafruit MiniMQTT client library for connecting to MQTT pub/sub broker: https://docs.circuitpython.org/projects/minimqtt/en/stable/api.html


@author Gina Sprint
@date 5/6/25
"""
import os
import ast
import ssl

from paho.mqtt import client as mqtt_client
import streamlit as st
import streamlit_authenticator as stauth
from streamlit_authenticator.utilities import LoginError
from openai import OpenAI


TOPIC = "/signs/office"
broker = port = username = password = None

# get sensitive info from Streamlit secrets
client = OpenAI(api_key=st.secrets.get("OPENAI_API_KEY"))

def connect_mqtt(broker, port, username, password, client_id):
    def on_connect(client, userdata, flags, rc, properties):
        if rc == 0:
            print("Connected to MQTT Broker!")
        else:
            print("Failed to connect, return code %d\n", rc)

    client = mqtt_client.Client(client_id=client_id, callback_api_version=mqtt_client.CallbackAPIVersion.VERSION2)
    # Set CA certificate
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    # ssl_ctx.verify_mode = ssl.CERT_NONE
    client.tls_set_context(ssl_ctx)
    client.tls_insecure_set(True)
    # client.tls_set(ca_certs='./emqxsl-ca.crt')
    client.username_pw_set(username, password)
    client.on_connect = on_connect
    client.connect(broker, port)
    return client

def publish(client, msg):
    result = client.publish(TOPIC, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        print(f"Send `{msg}` to topic `{TOPIC}`")
    else:
        print(f"Failed to send message to topic {TOPIC} {result[0]} {result[1]}")

def run(broker, port, username, password, client_id, msg):
    client = connect_mqtt(broker, port, username, password, client_id)
    client.loop_start()
    if msg is not None:
        publish(client, msg)
    client.loop_stop()

def clean_content(content):
    # remove extra lines
    lines = content.split("\n")
    code = " ".join(lines[1:])
    return lines[0], code

def mqtt_setup_and_publish(msg):
    client_id = st.secrets.get("MQTT_CLIENT_ID")
    broker = st.secrets.get("MQTT_BROKER")
    port = st.secrets.get("MQTT_PORT")
    username = st.secrets.get("MQTT_USERNAME")
    password = st.secrets.get("MQTT_PASSWORD")
    run(broker, port, username, password, client_id, msg)

def is_rgb_tuple(obj):
    return (
        isinstance(obj, tuple)
        and len(obj) == 3
        and all(isinstance(c, int) and 0 <= c <= 255 for c in obj)
    )

def is_static_config(obj):
    return (
        isinstance(obj, list)
        and len(obj) == 19
        and all(is_rgb_tuple(t) for t in obj)
    )

def is_dynamic_config(obj):
    if not isinstance(obj, list):
        return False
    for item in obj:
        if not isinstance(item, dict):
            return False
        if "lights" not in item or "delay" not in item:
            return False
        if not is_static_config(item["lights"]):
            return False
        if not (isinstance(item["delay"], int) or isinstance(item["delay"], float)):
            return False
    return True

def safe_eval_lighting_config(code_str):
    try:
        obj = ast.literal_eval(code_str)
    except (ValueError, SyntaxError):
        return "Error: Code in the response is not deemed safe enough to execute."

    if is_static_config(obj):
        return "Configuration: Static\n" + repr(obj)
    elif is_dynamic_config(obj):
        return "Configuration: Dynamic\n" + repr(obj)
    else:
        return "Error: Input is not a valid static or dynamic configuration."
    
prompt = \
"""You will be given a description of how someone wants to turn on 19 LED RGBW lights in a strip.
Parse their description into lists of (R, G, B) tuples using one of two configurations: static or dynamic.
Static is simply a Python list of 19 (R, G, B) tuples: [(255, 0, 0), (0, 255, 0), ...]
Dynamic is a Python list of dictionaries where each dictionary represents lights to show for a time delay in seconds: [{"lights": <list of 19 (R, G, B) tuples, "delay": <number of seconds to show the lights for}, ...]
Only use the Dynamic configuration if there is more than one list of 19 (R, G, B) tuples.

Example 1
Description: Turn the lights on so they look like a rainbow.
Configuration: Static
[(255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (75, 0, 130), (148, 0, 211), (255, 0, 0), (255, 127, 0), (255, 255, 0), (0, 255, 0), (0, 255, 255), (0, 0, 255), (75, 0, 130), (148, 0, 211), (255, 0, 0), (255, 127, 0), (255, 255, 0)]

Example 2
Description: Every second, alternative green and red, like a Christmas tree.
Configuration: Dynamic
[{"lights": [(255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0)], "delay": 1},
{"lights": [(0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0), (255, 0, 0), (0, 255, 0)], "delay": 1}]

Now, given the following description, parse a valid configuration response.
Respond with the configuration only in the form "Configuration: Static" or "Configuration: Dynamic" then the appropriate Python list on the next line. Do not include any additional newlines or markdown formatting.
If you are unable to parse a valid configuration, return:
"Error: <reason>" 
"""

# Creating the authenticator object
authenticator = None
if os.path.exists("config.yaml"):
    authenticator = stauth.Authenticate(
        'config.yaml'
    )
else:
    username = st.secrets.get("GUEST_USERNAME")
    email = st.secrets.get("GUEST_EMAIL")
    first = st.secrets.get("GUEST_FIRST_NAME")
    last = st.secrets.get("GUEST_LAST_NAME")
    hashed_password = st.secrets.get("GUEST_HASHED_PW")
    creds = {'usernames': 
                {username: 
                    {'email': email, 
                    'failed_login_attempts': 0, 
                    'first_name': first, 
                    'last_name': last, 
                    'logged_in': False, 
                    'password': hashed_password
                    }
                }
            }
    authenticator = stauth.Authenticate(
        creds,
        "ai_lights_name", # cookie name
        "ai_lights_key", # cookie key
        1 # cookie expiry days
    )

st.title("AI Lights Changer")

# Creating a login widget
try:
    authenticator.login()
except LoginError as e:
    st.error(e)

if st.session_state["authentication_status"]:
    authenticator.logout()
    st.write(f'Welcome *{st.session_state["name"]}*')
    with st.form("my_form"):
        user_description = st.text_input("Lights Description", "")
        # Every form must have a submit button.
        submitted = st.form_submit_button("Submit")
        if submitted:
            completion = client.chat.completions.create(
            model="o4-mini-2025-04-16",
            #model="gpt-4o-2024-08-06",
            messages=[
                    {"role": "developer", "content": "You are a helpful assistant."},
                    {
                        "role": "user",
                        "content": prompt + user_description
                    }
                ]
            )
            content = completion.choices[0].message.content
            st.write(content)
            # error checking to make sure content conforms to format
            # and only contains RGB tuples and delay #s
            config, code = clean_content(content)
            result = safe_eval_lighting_config(code)
            if "error" not in result.lower():
                st.write("No errors detected. Sending message to lighted sign!!")
                cleaned_content = config + "\n" + code
                mqtt_setup_and_publish(cleaned_content)
            else:
                st.write(result)
elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')
elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')
