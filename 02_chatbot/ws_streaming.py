from fasthtml.common import *
from claudette import *
import asyncio

# Set up the app, including daisyui and tailwind for the chat component
tlink = Script(src="https://cdn.tailwindcss.com"),
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")
app = FastHTML(hdrs=(tlink, dlink, picolink), ws_hdr=True)

# Set up a chat model client and list of messages (https://claudette.answer.ai/)
cli = Client(models[-1])
sp = """You are a helpful and concise assistant."""
messages = []

# Chat message component (renders a chat bubble)
# Now with a unique ID for the content and the message
def ChatMessage(msg_idx, **kwargs):
    msg = messages[msg_idx]
    bubble_class = f"chat-bubble-{'primary' if msg['role'] == 'user' else 'secondary'}"
    chat_class = f"chat-{'end' if msg['role'] == 'user' else 'start'}"
    return Div(Div(msg['role'], cls="chat-header"),
               Div(msg['content'], 
                   id=f"chat-content-{msg_idx}", # Target if updating the content
                   cls=f"chat-bubble {bubble_class}"),
               id=f"chat-message-{msg_idx}", # Target if replacing the whole message
               cls=f"chat {chat_class}", **kwargs)

# The input field for the user message. Also used to clear the 
# input field after sending a message via an OOB swap
def ChatInput():
    return Input(type="text", name='msg', id='msg-input', 
                 placeholder="Type a message", 
                 cls="input input-bordered w-full", hx_swap_oob='true')

# The main screen
@app.route("/")
def get():
    page = Body(H1('Chatbot Demo'),
                Div(*[ChatMessage(msg) for msg in messages],
                    id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"),
                Form(Group(ChatInput(), Button("Send", cls="btn btn-primary")),
                    ws_send="", hx_ext="ws", ws_connect="/wscon",
                    cls="flex space-x-2 mt-2",
                ), 
                cls="p-4 max-w-lg mx-auto",
                ) # Open a websocket connection on page load
    return Title('Chatbot Demo'), page


@app.ws('/wscon')
async def ws(msg:str, send): 
    messages.append({"role":"user", "content":msg})

    # Send the user message to the user (updates the UI right away)
    await send(Div(ChatMessage(len(messages)-1), hx_swap_oob='beforeend', id="chatlist"))

    # Send the clear input field command to the user
    await send(ChatInput())

    # Model response (streaming)
    r = cli(messages, sp=sp, stream=True)

    # Send an empty message with the assistant response
    messages.append({"role":"assistant", "content":""}) 
    await send(Div(ChatMessage(len(messages)-1), hx_swap_oob='beforeend', id="chatlist")) 

    # Fill in the message content  
    for chunk in r:
        messages[-1]["content"] += chunk
        await send(Span(chunk, id=f"chat-content-{len(messages)-1}", hx_swap_oob="beforeend"))
        await asyncio.sleep(0.5) # Simulate a delay

if __name__ == '__main__': uvicorn.run("ws_streaming:app", host='0.0.0.0', port=8000, reload=True)