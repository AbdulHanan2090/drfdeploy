from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
import nltk
from nltk.stem import WordNetLemmatizer
import json
import pickle
import numpy as np
import random
import os
from keras.models import load_model
import ffmpeg
import openai
import os
import openai
import speech_recognition as sr
from pydub.utils import mediainfo
from pathlib import Path

lemmatizer = WordNetLemmatizer()
# words = []
# classes = []
# documents = []
# ignore_words = ['?', '!']
nltk.download('punkt')  # unsuperviesd
nltk.download('wordnet')  # dict
nltk.download('omw-1.4')  # VACABLARY
# data_file = open('intents.json', encoding='utf-8').read()
# intents = json.loads(data_file)
# nltk.download('punkt')  # unsuperviesd
# nltk.download('wordnet')  # dict
# nltk.download('omw-1.4')  # VACABLARY
# for intent in intents['intents']:
#     for pattern in intent['patterns']:

#         # tokenize each word
#         w = nltk.word_tokenize(pattern)
#         words.extend(w)
#         # add documents in the corpus
#         documents.append((w, intent['tag']))

#         # add to our classes list
#         if intent['tag'] not in classes:
#             classes.append(intent['tag'])

# words = [lemmatizer.lemmatize(w.lower())
#          for w in words if w not in ignore_words]
# words = sorted(list(set(words)))

# # sort classes
# classes = sorted(list(set(classes)))

# # documents = combination between patterns and intents
# print(len(documents), "documents")

# # classes = intents
# print(len(classes), "classes", classes)

# # words = all words, vocabulary
# print(len(words), "unique lemmatized words", words)

# # creating a pickle file to store the Python objects which we will use while predicting
# pickle.dump(words, open('words.pkl', 'wb'))
# pickle.dump(classes, open('classes.pkl', 'wb'))
# # create our training data
# training = []

# # create an empty array for our output
# output_empty = [0] * len(classes)

# # training set, bag of words for each sentence
# for doc in documents:
#     # initialize our bag of words
#     bag = []
#     # list of tokenized words for the pattern
#     pattern_words = doc[0]

#     # lemmatize each word - create base word, in attempt to represent related words
#     pattern_words = [lemmatizer.lemmatize(
#         word.lower()) for word in pattern_words]

#     # create our bag of words array with 1, if word match found in current pattern
#     for w in words:
#         bag.append(1) if w in pattern_words else bag.append(0)
#     # output is a '0' for each tag and '1' for current tag (for each pattern)
#     output_row = list(output_empty)
#     output_row[classes.index(doc[1])] = 1
#     training.append([bag, output_row])

# # shuffle features and converting it into numpy arrays
# random.shuffle(training)
# training = np.array(training, dtype=object)

# # create train and test lists

# train_x = list(training[:, 0])
# train_y = list(training[:, 1])
# print(len(train_x[0]))

# # Create NN model to predict the responses

# print("Training data created"+f"{training}")

# model = Sequential()

# model.add(Dense(128, input_shape=(len(train_x[0]),), activation='relu'))
# model.add(Dropout(0.5))
# model.add(Dense(64, activation='relu'))
# model.add(Dropout(0.5))
# model.add(Dense(len(train_y[0]), activation='softmax'))

# # Compile model. Stochastic gradient descent with Nesterov accelerated gradient gives good results for this model
# sgd = SGD(learning_rate=0.01, decay=1e-6, momentum=0.9, nesterov=True)
# model.compile(loss='categorical_crossentropy',
#               optimizer=sgd, metrics=['accuracy'])

# # fitting and saving the model
# hist = model.fit(np.array(train_x), np.array(train_y),
#                  epochs=200, batch_size=5, verbose=1)
# model.save('chatbot.h5', hist)
# # we will pickle this model to use in the future

# print("\n")
# print("*"*50)
# print("\nModel Created Successfully!")
# # load the saved model file
model = load_model('chatbot.h5')
intents = json.loads(open("intents.json", encoding='utf-8').read())
words = pickle.load(open('words.pkl', 'rb'))
classes = pickle.load(open('classes.pkl', 'rb'))


def clean_up_sentence(sentence):

    # tokenize the pattern - split words into array
    sentence_words = nltk.word_tokenize(sentence)

    # stem each word - create short form for word
    sentence_words = [lemmatizer.lemmatize(
        word.lower()) for word in sentence_words]
    return sentence_words


def bow(sentence, words, show_details=True):

    # tokenize the pattern
    sentence_words = clean_up_sentence(sentence)

    # bag of words - matrix of N words, vocabulary matrix
    bag = [0]*len(words)
    for s in sentence_words:
        for i, w in enumerate(words):
            if w == s:

                # assign 1 if current word is in the vocabulary position
                bag[i] = 1
                if show_details:
                    print("found in bag: %s" % w)
    return (np.array(bag))


def predict_class(sentence, model):

    # filter out predictions below a threshold
    p = bow(sentence, words, show_details=False)
    res = model.predict(np.array([p]))[0]
    error = 0.25
    results = [[i, r] for i, r in enumerate(res) if r > error]

    # sort by strength of probability
    results.sort(key=lambda x: x[1], reverse=True)
    return_list = []

    for r in results:
        return_list.append({"intent": classes[r[0]], "probability": str(r[1])})
    return return_list
    # function to get the response from the model


def getResponse(ints, intents_json):
    tag = ints[0]['intent']
    list_of_intents = intents_json['intents']
    for i in list_of_intents:
        if (i['tag'] == tag):
            result = random.choice(i['responses'])
            break
    return result


def chatbot_response(text):
    ints = predict_class(text, model)
    res = getResponse(ints, intents)
    return res


class ChatCheck(APIView):
    def get(self, request, data):
        return Response({"Replay": chatbot_response(data), "status": status.HTTP_200_OK})


class Check(APIView):
    def get(self, request):
        return Response({"status": status.HTTP_200_OK})
def lec_process(filename, chunk_duration=90):

    record = sr.Recognizer()

    with sr.AudioFile(filename) as source:

        lec_data = mediainfo(filename)

        lec_duration = int(float(lec_data['duration']))

        data_material = ""

        for i in range(0, lec_duration, chunk_duration):

            lec_chunk = record.record(source, duration=chunk_duration)

            data_material += record.recognize_google(lec_chunk) + " "
            
        return data_material
    
#lecturer summarizer part with different option



class Filesummary(APIView):
    def post(self, request):
        try:
            uploaded_file = request.FILES['video']
            # Assuming the file is in memory, you can read its content directly
            file_content = uploaded_file.read()

            # Now you can process the file content as needed
            # For example, you can save it to a temporary file or process it directly

            # Save the content to a temporary file (optional)
            with open('temp_video.mp4', 'wb') as temp_file:
                temp_file.write(file_content)

            # Process the temporary file or file_content as needed

            # Example processing using ffmpeg
            output_audio = 'output_audio.wav'
            ffmpeg.input('temp_video.mp4').output(output_audio).run(overwrite_output=True)

            # Example text extraction using lec_process
            Text_extraction = lec_process(output_audio)

            return Response({"Translation": Text_extraction, "status": status.HTTP_200_OK})
        except Exception as e:
            print('Error:', str(e))
            return Response({"error": "An error occurred", "status": status.HTTP_400_BAD_REQUEST})
