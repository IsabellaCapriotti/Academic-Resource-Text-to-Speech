from dotenv import load_dotenv
from google.cloud import texttospeech
import os 
import subprocess
import mimetypes
import pdfplumber
from tkinter import * 
from tkinter import ttk 
import tkinter.font as font 
from tkinter.scrolledtext import ScrolledText

# Read environment vars from config file
load_dotenv()

# Voice config vars
VOICES = ['en-US-Standard-A','en-US-Standard-B','en-US-Standard-C','en-US-Standard-D','en-US-Standard-E','en-US-Standard-F','en-US-Standard-G','en-US-Standard-H','en-US-Standard-I','en-US-Standard-J','en-US-Wavenet-A','en-US-Wavenet-B','en-US-Wavenet-C','en-US-Wavenet-D','en-US-Wavenet-E','en-US-Wavenet-F','en-US-Wavenet-G','en-US-Wavenet-H','en-US-Wavenet-I','en-US-Wavenet-J']
DEFAULT_VOICE = 'en-US-Wavenet-D'

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

def gen_mp3(raw_text, filename, voice=DEFAULT_VOICE):
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

        voice_config = texttospeech.VoiceSelectionParams(language_code="en-US", name=voice)  

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

# Opens the newly created MP3 file in the system's default music player. 
def open_mp3(filename):
    base_path = os.getcwd()
    path = '"' + base_path + "\\" + filename + '.mp3"'
    os.startfile(path, 'open')

#############################################
# TKINTER EVENT CALLBACKS
#############################################
# Fetches the raw text from the text entry when the button to 
# generate an MP3 file is clicked.
def on_gen_mp3_btn_click():

    # Read text 
    text = text_entry.get('1.0', 'end')
    print('got text', text)
    loading.grid(row=6, column=4)
    
    # Read current voice selection
    voice_idx = voice_listbox.curselection()[0]

    gen_mp3(text, filename_entry.get(), VOICES[voice_idx])
    loading.grid_remove()

    # Open MP3 file automatically if option is checked
    if open_mp3_check_val.get():
        open_mp3(filename_entry.get())

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
root_frame.columnconfigure(0, weight=2)
root_frame.columnconfigure(3, weight=1)
root_frame['padding'] = 20 

# Text entry 
text_entry_lbl = ttk.Label(root_frame, text="Enter text to read:", font=("TkHeadingFont", 22))
text_entry_lbl.grid(row=0, column=0, columnspan=2, sticky=(N,W))

text_entry = ScrolledText(root_frame, width=10, height=30)
text_entry.grid(row=1, column=0, rowspan=3, columnspan=3, sticky=(E,W))

# Enable paste into text entry 
text_entry.bind('<ButtonPress-3>', on_entry_paste)

# Options Menu 
options_menu = ttk.Frame(root_frame)
options_menu.grid(row=1, column=3)
options_lbl = ttk.Label(root_frame, text="Options",font=("TkHeadingFont", 22))
options_lbl.grid(row=0, column=3)

# Automatic MP3 open
open_mp3_check_val = BooleanVar(value=True)
open_mp3_check = ttk.Checkbutton(options_menu, text='Open MP3 file automatically?', variable=open_mp3_check_val, onvalue=True, offvalue=False)
open_mp3_check.grid(row=2, column=0)

# Voice select 
voice_select_lbl = ttk.Label(options_menu, text='Voice Select')
voice_select_lbl.grid(row=3, column=0)

voice_select_outer = ttk.Frame(options_menu)
voice_select_outer.grid(row=4, column=0)

voices_var = StringVar(value=VOICES)
voice_listbox = Listbox(voice_select_outer, height=10, listvariable=voices_var)
voice_listbox.grid(row=0, column=0, sticky=(N,S,E,W))
voice_listbox.selection_set(VOICES.index(DEFAULT_VOICE))
voice_listbox.see(VOICES.index(DEFAULT_VOICE))

voice_scrollbar = ttk.Scrollbar(voice_select_outer, orient=VERTICAL, command=voice_listbox.yview)
voice_listbox.configure(yscrollcommand=voice_scrollbar.set)
voice_scrollbar.grid(column=1, row=0, sticky=(N,S))

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