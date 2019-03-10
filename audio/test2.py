from google.cloud import speech_v1p1beta1 as speech
client = speech.SpeechClient()

speech_file = 'drake.wav'

with open(speech_file, 'rb') as audio_file:
    content = audio_file.read()

audio = speech.types.RecognitionAudio(content=content)

config = speech.types.RecognitionConfig(
    encoding=speech.enums.RecognitionConfig.AudioEncoding.LINEAR16,
    sample_rate_hertz=16000,
    language_code='en-US',
    enable_word_confidence=True)

response = client.recognize(config, audio)

for i, result in enumerate(response.results):
    alternative = result.alternatives[0]
    print('-' * 20)
    print('First alternative of result {}'.format(i))
    print(u'Transcript: {}'.format(alternative.transcript))
    print(u'First Word and Confidence: ({}, {})'.format(
        alternative.words[0].word, alternative.words[0].confidence))