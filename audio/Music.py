import numpy as np
import librosa
import librosa.display

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

    mask_v = librosa.util.softmask(S_full - S_filter,
                                   margin_v * S_filter,
                                   power=power)

    S_foreground = mask_v * S_full
    res = librosa.istft(S_foreground * phase)

    librosa.output.write_wav(new_path, res, sr)


def get_lyrics(path):
    import requests
    import json
    import re
    import string

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
