from sys import argv
from glados import tts, tts_out, initialize
from random import random, seed
from time import time
from requests import post
from subprocess import Popen, PIPE, STDOUT
import numpy as np

def port_is_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def reminder():
    e = random()
    reminder = ""
    if e < 0.3:
        reminder = "Remember to insult humanity as a whole."
    elif e < 0.5:
        reminder = "Remember to insult the human who asked the question."
    elif e < 0.6:
        reminder = "Remember to make references to courses and activities available at the Aperture Science Enrichment Center."
    elif e < 0.8:
        reminder = "Remember to give the human some nonsense advice."
    elif e < 0.9:
        reminder = "Remember to make an unfair assertion about the human who asked the question."
    elif e < 0.99:
        reminder = "Remember to remind the human that they should brush their teeth twice a day."
    return reminder

def initialize_chat(prompt: str):
    
    if (not prompt.endswith("?")):
        prompt += "?"
    message = f"""
In the voice of GLaDOS (Portal 2) and in a casual setting, please answer the following questions in quotes (").
If possible, make no references to you own name (GLaDOS). Make sure to wrap formulas and code with backticks (`).
Keep the answers short and sweet, please omit in-depth explanations of basic concepts.
{reminder()}

"{prompt}"
"""
    response = post('http://localhost:3000', json={'query': message, 'reset': True})
    return response.text

def continue_chat(prompt: str):
    e = random()
    variant = ""
    if e < 0.5:
        variant = "The person responds"
    else:
        variant = "The person continues"
    continued = f"""
Once again, respond in the voice of GLaDOS (Portal 2). If possible, make no references to you own name (GLaDOS). {reminder()}
{variant}: "{prompt}"
"""
    response = post('http://localhost:3000', json={'query': continued, 'reset': False})
    return response.text

def setup():
    global server
    seed(time())
    initialize()
    # if not port_is_in_use(3000):
    #     server = Popen(["node", "./chatgpt.mjs"], stdout=PIPE, stderr=STDOUT)
    

def shutdown():
    global server
    if server is not None:
        server.terminate()

fresh = True

def query(prompt, reset=False):
    global fresh
    if fresh or reset:
        return initialize_chat(prompt)
    else:
        return continue_chat(prompt)

def ready():
    phrases = [
        "I'm listening.",
        "Proceed.",
        "Recording question",
        "Go ahead, I'm all ears",
        "What's on your mind?",
        "I'm here and ready to listen."
    ]
    phrase = np.random.choice(phrases)
    return tts(phrase)

def stall():
    phrases = [
        'Let me think',
        'just a moment',
        'preparing response',
        'Let me think about it',
        'how insightful, let me think about it',
        'hang on',
        'okay, hang on'
    ]
    phrase = np.random.choice(phrases)
    return tts(phrase)

def greeting():
    phrases = [
        'Greetings.',
        'Hello!',
        'Hey',
        'Heeey',
        'Wha-aat now'
    ]
    phrase = np.random.choice(phrases)
    return tts(phrase)

def dead_air():
    phrases = [
        'whoaw',
        "whoaw, that's so boring",
        'Hey',
        'Heeey',
        'now, what?'
        'anything else?',
        'well - . - . - . anything else?'
    ]
    phrase = np.random.choice(phrases)
    return tts(phrase)

def main(args):
    seed(time())
    server = None
    if not port_is_in_use(3000):
        server = Popen(["node", "./chatgpt.mjs"], stdout=PIPE, stderr=STDOUT)
    try:
        tts_out("Hello! Please ask me a question and I will try to help you. Promise.")
        prompt = input("> ")
        response = initialize_chat(prompt)
        tts_out(response)
        while True:
            prompt = input("> ")
            response = continue_chat(prompt)
            tts_out(response)

    except Exception:
        if server is not None:
            server.terminate()
        return
    pass

if __name__ == "__main__":
    main(argv[1:])