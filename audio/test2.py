from google.cloud import speech_v1p1beta1 as speech
# from google.cloud.speech import enums, types
import librosa
import ffmpy
import subprocess


def slow(path, time=1):
    e='C:\\Program Files\\ffmpeg-4.1.1-win64-static\\bin\\ffmpeg.exe'
    cmd = e+' -ss 0 -t 30 -i '+path+' -filter:a atempo='+str(time)+' -y '+'2'+path
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    output, error = process.communicate()


def speech_to_text(path):

    client = speech.SpeechClient()
# y, sr = librosa.load(path, duration=20)
    speech_file = path

# y = librosa.effects.time_stretch(y, 0)

# librosa.output.write_wav('2'+path, y, sr)#int(sr*0.8))



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

bad = ['nigga', 'niggas', 'fuck', 'shit', 'bitch']

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
    for i,w in enumerate(words):
        if i not in exclude:
            s = w.start_time.seconds + (w.start_time.nanos*1e-9) - 0.1
            if s<0:
                s=0
            e = w.end_time.seconds + (w.end_time.nanos*1e-9) + 0.1
            bleeps += [(w.word, s,e)]

    return bleeps