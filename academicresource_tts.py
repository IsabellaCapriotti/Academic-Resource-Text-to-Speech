from dotenv import load_dotenv
from google.cloud import texttospeech
import os 
import mimetypes
import pdfplumber

# Read environment vars from config file
load_dotenv()

#############################################
# PROCESSING FILE 
#############################################

# Get path of input file
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
    
#############################################
# TTS API CALLS
#############################################

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

    voice_config = texttospeech.VoiceSelectionParams(language_code="en-US", name='en-US-Standard-F') # For WaveNet: en-US-Wavenet-H

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