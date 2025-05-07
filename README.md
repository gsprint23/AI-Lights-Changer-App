# Welcome to the AI Lights Changer App!
(this is the quick README... if I have more time later I'll write a more detailed one 🤓)  
Describe how you want to light the sign up and the app will use AI to parse executable code from your prompt that is sent to the sign to light it up. You can play with the deployed version on Streamlit Cloud: https://ai-lights-changer.streamlit.app/ (however, you'll need a username and password to access it...)

To make this all work, this app uses:
* Streamlit for the web framework and cloud deployment: https://streamlit.io/
* Streamlit Authenticator for authentication: https://github.com/mkhorasani/Streamlit-Authenticator
* OpenAI API for LLM access: https://platform.openai.com/docs/overview
* Paho MQTT client library for connecting to MQTT pub/sub broker: https://pypi.org/project/paho-mqtt/
* EMQX for the MQTT pub/sub broker: https://www.emqx.com/en

Note: the lights in the sign are controlled by an ESP32 running CircuitPlayground and the
Adafruit MiniMQTT client library for connecting to MQTT pub/sub broker: https://docs.circuitpython.org/projects/minimqtt/en/stable/api.html
