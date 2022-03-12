from dotenv import load_dotenv
from google.cloud import texttospeech
import os 
import mimetypes
import pdfplumber
from tkinter import * 
from tkinter import ttk 
import tkinter.font as font 
from tkinter.scrolledtext import ScrolledText

# Read environment vars from config file
load_dotenv()

#############################################
# PROCESSING FILE 
#############################################

# Get path of input file
def get_input_file():
    valid_file = False

    while not valid_file:
        filepath = input('Enter the file path of text to read:')
        
        # If file is found, infer its type
        if os.path.isfile(filepath):
            type = mimetypes.guess_type(filepath)
            valid_file = True
        # If file wasn't found, print an error message and try again 
        else:
            print('Couldn\'t find your file. Please enter a valid path.')
            valid_file = False

    # Get raw text from file
    filename = os.path.basename(filepath)
    print('Processing file ' + filename)
    mime_type = type[0]
    raw_text = ''

    #############################################
    # CONVERSION TO RAW TEXT
    #############################################

    # For plain text, can read directly
    if mime_type == 'text/plain': 
        print('Detected plain text file.')
        raw_text = open(filepath).read()

    # Extract text from PDF
    elif mime_type == 'application/pdf':
        print('Detected PDF.', end='')

        # Option to write converted PDF to txt file for future use
        write_plain_text = input(' Generate plain text output file? (Y/N) ')
        if(write_plain_text.lower() == 'y'):
            write_plain_text = True
        else:
            write_plain_text = False

        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                raw_text += page.extract_text()

        # Write pdf raw text to file if desired
        if write_plain_text:
            txt_output = open(filename + '.txt', 'w')
            txt_output.write(raw_text)
            txt_output.close()
            print('Generated raw text file ' + filename + '.txt.')

    else:
        print('Unsupported file type. Currently, the tool only supports .txt and .pdf files.')
        exit()

    return raw_text
        
#############################################
# TTS API CALLS
#############################################

def gen_mp3(raw_text, filename):
    # Each request can only handle 5000 characters of input, so break raw text into 5000-character chunks
    curr_offset = 0 
    complete_audio = b''
    requests_sent = 0 

    while(curr_offset < len(raw_text)):
        curr_chunk = raw_text[curr_offset:curr_offset+5000]
        curr_offset += 5000
        requests_sent += 1

        # Initialize connection to API 
        client = texttospeech.TextToSpeechClient()

        # Configure voice and audio format
        to_speak = texttospeech.SynthesisInput(text=curr_chunk)

        voice_config = texttospeech.VoiceSelectionParams(language_code="en-US", name='en-US-Wavenet-D')  

        audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

        # Get response
        res = client.synthesize_speech(input=to_speak, voice=voice_config, audio_config=audio_config)
        complete_audio += res.audio_content


    #############################################
    # GENERATE MP3 FILE
    #############################################
    print('Number of characters sent: ' + str(len(raw_text)))
    print('Number of requests sent: ' + str(requests_sent))

    # Write to file
    with open(filename + ".mp3", "wb") as out: 
        out.write(complete_audio)

    print('Created audio file ' + filename + '.mp3')


#############################################
# TKINTER EVENT CALLBACKS
#############################################
# Fetches the raw text from the text entry when the button to 
# generate an MP3 file is clicked.
def on_gen_mp3_btn_click():
    text = text_entry.get('1.0', 'end')
    print('got text', text)
    loading.grid(row=6, column=4)

    gen_mp3(text, filename_entry.get())
    loading.grid_remove()

# Inserts the text on the clipboard to the current cursor position
# when a right click is triggered on the entry box. 
def on_entry_paste(e):
    idx = text_entry.index('insert')
    text_entry.insert(idx, root.clipboard_get())

#############################################
# TKINTER LAYOUT
#############################################

# Main window and frame 
root = Tk()
root.title("Text To Speech")
root.columnconfigure(0, weight=1)

root_frame = ttk.Frame(root)
root_frame.grid(row=0,column=0, sticky=(N,S,E,W))
root_frame.columnconfigure(0, weight=1)
root_frame['padding'] = 20 

# Text entry 
text_entry_lbl = ttk.Label(root_frame, text="Enter text to read:", font=("TkHeadingFont", 22))
text_entry_lbl.grid(row=0, column=0, columnspan=2, sticky=(N,W))

text_entry = ScrolledText(root_frame, width=10, height=30)
text_entry.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=(E,W))
# text_entry = Text(root_frame, width=10, height=30)
# text_entry.grid(row=1, column=0, rowspan=3, columnspan=4, sticky=(E,W))

# scroll = ttk.Scrollbar(text_entry, orient=VERTICAL, command=text_entry.yview)
# text_entry.configure(yscrollcommand=scroll.set)
# scroll.pack(side=RIGHT)

# Enable paste into text entry 
text_entry.bind('<ButtonPress-3>', on_entry_paste)

# File name 
filename_frame = ttk.Frame(root_frame, padding=(0, 20))
filename_frame.grid(row=5, column=0, columnspan=5, sticky=(E,W))

filename_label = ttk.Label(filename_frame, text='Enter name to save MP3 file as: ', font=('TkDefault', 18))
filename_label.grid(row=5, column=0, columnspan=2, sticky=(W))

filename = StringVar()
filename_entry = ttk.Entry(filename_frame, textvariable=filename)
filename_entry.insert(0, 'out')
filename_entry.grid(row=5, column=2, columnspan=3, sticky=(W))

# MP3 creation
s = ttk.Style()
s.configure('MP3.TButton', foreground='blue', font=('TkDefault', 18))
gen_mp3_btn = ttk.Button(root_frame, text='Generate MP3 file', command=on_gen_mp3_btn_click, style='MP3.TButton')
gen_mp3_btn.grid(row=6, column=0, columnspan=3)

# Loading wheel 
loading = ttk.Label(root_frame, text='Loading...')

# # Strobe text
# s = ttk.Style()
# strobe_window = ttk.Frame(root)
# strobe_window.columnconfigure(1, weight=1)
# strobe_window.grid(row=0, column=7, columnspan=3)

# strobe_lbl = ttk.Label(strobe_window)
# strobe_lbl.grid(row=0, column=0)

root.mainloop()