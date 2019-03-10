import numpy as np
import librosa
import librosa.display
from google.cloud import speech_v1p1beta1 as speech
import subprocess
import requests
import json
import re
import string
import soundfile

bad = ['nigga', 'niggas', 'fuck', 'shit', 'bitch', 'shit', 'dick', 'tits', 'fucker',
       'fucking', 'hoe', 'asshole', 'whore', 'homo', 'ho', 'ass', 'stupid-ass', 'motherfucker']

def slow(path, time=1):
    e='C:\\Program Files\\ffmpeg-4.1.1-win64-static\\bin\\ffmpeg.exe'
    cmd = e+' -ss 0 -t 30 -i '+path+' -filter:a atempo='+str(time)+' -y '+'2'+path
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = process.communicate()


def speech_to_text(path):

    client = speech.SpeechClient()
    speech_file = path

    with open(speech_file, 'rb') as audio_file:
        content = audio_file.read()
    audio = speech.types.RecognitionAudio(content=content)

    config = speech.types.RecognitionConfig(
        # encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
        # sample_rate_hertz=16000,
        # sample_rate_hertz=int(sr*0.8),
        max_alternatives=5,
        language_code='en-US',
        enable_word_confidence=True,
        enable_word_time_offsets=True,
        model="video")

    response = client.recognize(config, audio)

    for i, result in enumerate(response.results):
        alternative = result.alternatives[0]
        print('-' * 20)
        print('First alternative of result {}'.format(i))
        print(u'Transcript: {}'.format(alternative.transcript))
        print(u'First Word and Confidence: ({}, {})'.format(
            alternative.words[0].word, alternative.words[0].confidence))

    return response.results

def clean(alt):
    return alt[0].alternatives[0].transcript.split(" ")

def cleaner(alt, lyrics):
    words = alt[0].alternatives[0].words
    wlist = [x.word for x in words]
    occr = []
    bleeps = []
    include = set()
    prv=0
    for i,w in enumerate(wlist):
        if w in words[prv:]:
            idx = words[prv:].index(w)
            if idx-prv<3:
                occr += [idx]
                prv = idx
            else:
                occr += ['fail']
        else:
            occr+=['fail']
    for i,q in enumerate(wlist):
        if words[i] in bad and occr[i]=='fail':
            iprev = -1
            inext = len(words)
            for j in range(i-1, -1, -1):
                if occr[j]!='fail':
                    iprev=occr[j]
                    break
            for j in range(i+1, len(words)):
                if occr[j]!='fail':
                    inext=occr[j]
                    break
            if inext-iprev < 3:
                # start = words[iprev+1].start_time.seconds + words[iprev+1].start_time.nanos * 1e-9
                # end = words[inext-1].end_time.seconds + words[inext-1].end_time.nanos * 1e-9

                include+={x for x in range(iprev+1, inext)}
        elif words[i] in bad:
            include+={occr[i]}
    for i,w in enumerate(words):
        if i in include or w.word in bad:
            s = w.start_time.seconds + (w.start_time.nanos*1e-9)
            if s<0:
                s=0
            e = w.end_time.seconds + (w.end_time.nanos*1e-9)
            if s==e:
                s-=0.05
                e+=0.05
            bleeps += [(s,e)]
    return bleeps

def match(alt, lyrics):
    words = alt[0].alternatives[0].words
    wlist = [x.word for x in words]
    occr = []
    bleeps = []
    exclude = set()
    prv=0
    for i,w in enumerate(wlist):
        if w in words[prv:]:
            idx = words[prv:].index(w)
            if idx-prv<3:
                occr += [idx]
                prv = idx
            else:
                occr += ['fail']
        else:
            occr+=['fail']
    for i,q in enumerate(occr):
        if words[i] in bad and occr[i]=='fail':
            iprev = -1
            inext = len(words)
            for j in range(i-1, -1, -1):
                if occr[j]!='fail':
                    iprev=occr[j]
                    break
            for j in range(i+1, len(words)):
                if occr[j]!='fail':
                    inext=occr[j]
                    break
            if inext-iprev < 3:
                # start = words[iprev+1].start_time.seconds + words[iprev+1].start_time.nanos * 1e-9
                # end = words[inext-1].end_time.seconds + words[inext-1].end_time.nanos * 1e-9

                exclude+={x for x in range(iprev+1, inext)}
        elif words[i] in bad:
            exclude+={occr[i]}
    for i,w in enumerate(words):
        if i not in exclude and w.word not in bad:
            s = w.start_time.seconds + (w.start_time.nanos*1e-9)
            if s<0:
                s=0
            e = w.end_time.seconds + (w.end_time.nanos*1e-9)
            if s==e:
                s-=0.05
                e+=0.05
            bleeps += [(s,e)]
    return bleeps


def strip_vocal(path, new_path):
    y, sr = librosa.load(path)

    # And compute the spectrogram magnitude and phase
    S_full, phase = librosa.magphase(librosa.stft(y))

    S_filter = librosa.decompose.nn_filter(S_full,
                                           aggregate=np.median,
                                           metric='cosine',
                                           width=int(librosa.time_to_frames(2, sr=sr)))

    S_filter = np.minimum(S_full, S_filter)

    margin_i, margin_v = 2, 10
    power = 2

    mask_i = librosa.util.softmask(S_filter,
                                   margin_i * (S_full - S_filter),
                                   power=power)

    mask_v = librosa.util.softmask(S_full - S_filter,
                                   margin_v * S_filter,
                                   power=power)

    S_foreground = mask_v * S_full
    S_background = mask_i * S_full
    front = librosa.istft(S_foreground * phase)

    librosa.output.write_wav(new_path, front, sr)
    back = librosa.istft(S_background * phase)
    librosa.output.write_wav("back" + new_path, back, sr)

    front, back = pad(front, back)

    new = front *0.5 + back * 0.5

    #new = y-instruments
    librosa.output.write_wav("kanyenew1.wav", new, sr)

def divi(path):
    y, sr = librosa.load(path)

    # And compute the spectrogram magnitude and phase
    S_full, phase = librosa.magphase(librosa.stft(y))

    S_filter = librosa.decompose.nn_filter(S_full,
                                           aggregate=np.median,
                                           metric='cosine',
                                           width=int(librosa.time_to_frames(2, sr=sr)))

    S_filter = np.minimum(S_full, S_filter)

    margin_i, margin_v = 2, 10
    power = 2

    mask_i = librosa.util.softmask(S_filter,
                                   margin_i * (S_full - S_filter),
                                   power=power)

    mask_v = librosa.util.softmask(S_full - S_filter,
                                   margin_v * S_filter,
                                   power=power)

    S_foreground = mask_v * S_full
    S_background = mask_i * S_full
    front = librosa.istft(S_foreground * phase)
    back = librosa.istft(S_background * phase)

    return front, back, sr


def pad(l1, l2):
    diff = len(l1) - len(l2)

    if diff > 0:
        l2 = np.append(l2, np.zeros(diff))
    elif diff < 0:
        l1 = np.append(l1, np.zeros(-diff))

    return l1, l2


def instrumental(path, newpath):
    signal, Fs = soundfile.read(path)
    signal1 = signal[:, 0]
    signal2 = signal[:, 1]
    msignal = signal1 - signal2
    soundfile.write("1" + newpath, signal1, Fs)
    soundfile.write('2' + newpath, signal2, Fs)
    soundfile.write(newpath, msignal, Fs)


def get_lyrics(path):

    sample, sr = librosa.load(path, duration=18)
    filename = './trim.wav'
    librosa.output.write_wav(filename, sample, sr)

    # curl -F "api_token=test" -F "return=lyrics" -F "file=@vocals.wav" https://api.audd.io/

    files = {
        'api_token': (None, 'test'),
        'return': (None, 'lyrics'),
        'file': (filename, open(filename, 'rb')),
    }

    response = requests.post('https://api.audd.io/', files=files)

    lyrics = json.loads(response.content).get('result').get('lyrics').get('lyrics')

    # Remove annotations, punctuation, whitespace
    lyrics = re.sub("[\(\[].*?[\)\]]", "", lyrics).replace('\r', '')
    lyrics = list(filter(None, lyrics.translate(str.maketrans('', '', string.punctuation)).lower().split("\n ")))
    lyrics = list(filter(None, ' '.join(lyrics).split(' ')))

    return lyrics


def censor(vocals, times, sr=22050):

    for s, e in times:
        start = int(s * sr)
        end = int(e * sr)
        #vocals[start:end] = vocals[start:end][::-1]
        x = vocals[start:end] * 0
        np.random.shuffle(x)
        vocals[start:end] = x[:]

    return vocals


def runner(path):
    data = speech_to_text(path)
    lyrics = get_lyrics(path)
    matched_data = match(data, lyrics)
    v, i, sr = divi(path)
    v = censor(v, matched_data, sr)

    v, i = pad(v, i)
    new = v * 0.5 + i * 0.5
    librosa.output.write_wav("./out/explicit.wav", new, sr)

    matched_data = cleaner(data, lyrics)
    v, i, sr = divi(path)
    v = censor(v, matched_data, sr)

    v, i = pad(v, i)
    new = v * 0.5 + i * 0.5
    librosa.output.write_wav("./out/clean.wav", new, sr)

    return matched_data
