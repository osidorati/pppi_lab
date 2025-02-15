import sklearn
import telebot
from telebot import types
import json
import torch
from modelsp import NeuralNet
from nltk_utils import bag_of_words, tokenize
import random
import pandas as pd
import numpy as np
from sklearn.feature_extraction import text
from sklearn.metrics.pairwise import cosine_similarity


# bot connecting
keyboard1 = telebot.types.ReplyKeyboardMarkup()
keyboard1.row('Ok', 'Bye')

# input model variable
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

with open('intents.json', 'r', encoding='utf-8') as json_data:
    intents = json.load(json_data)

FILE = "data.pth"
data = torch.load(FILE)

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data['all_words']
tags = data['tags']
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size).to(device)
model.load_state_dict(model_state)
model.eval()

bot_name = "Sam"
print("Let's chat! (type 'quit' to exit)")


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет, я бот книжного магазина Буклет! Пишите свои вопросы', reply_markup=keyboard1)


@bot.message_handler(content_types=['text'])
def send_text(message):
    # if message.text.lower in ['донецк', 'макеевка', 'луганск']:
    #     if
    sentence = message.text
    sentence = tokenize(sentence)
    X = bag_of_words(sentence, all_words)
    X = X.reshape(1, X.shape[0])
    X = torch.from_numpy(X).to(device)

    output = model(X)
    _, predicted = torch.max(output, dim=1)

    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]
    if prob.item() > 0.75:
        for intent in intents['intents']:
            if tag == intent["tag"]:
                if tag == "адрес":
                    bot.send_message(message.chat.id, f"{random.choice(intent['responses'])}")
                    bot.register_next_step_handler(message, address)
                elif tag == "выбор книги":
                    bot.send_message(message.chat.id, f"{random.choice(intent['responses'])}")
                    bot.register_next_step_handler(message, choice_help)
                else:
                    bot.send_message(message.chat.id, f"{random.choice(intent['responses'])}")

    else:
        bot.send_message(message.chat.id, f"Bot: I do not understand..." + "\n")
        print(f"{bot_name}: I do not understand...")

#
# data = pd.read_csv('labirint_n.csv', converters={"Описание": lambda x: x.lower()}, encoding="1251", sep=';')
# books = data["Описание"].tolist()
# print(type(books))
# uni_tfidf = text.TfidfVectorizer(input=books)
#
# uni_matrix = uni_tfidf.fit_transform(books)
# uni_sim = cosine_similarity(uni_matrix)
# indices = pd.Series(data.index, index=data['Название']).drop_duplicates()
#


# def choice_help(message):
#     global book
#     book = message.text
#
#     data["Recommended_books"] = [recommend_articles(x) for x in uni_sim]
#
#     n = get_rec('Так говорил Заратустра. Книга для всех и ни для кого', uni_sim)
#     bot.send_message(message.chat.id, n)
#     bot.register_next_step_handler(message, send_text)
#
#
# def recommend_articles(x):
#     return ", ".join(data["Название"].loc[x.argsort()[-5:-1]])
#
#
# def get_rec(title, cosine_sim):
#     idx = indices[title]
#     sim_scores = list(enumerate(cosine_sim[idx]))
#     sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
#     sim_scores = sim_scores[1:11]
#     book_indices = [i[0] for i in sim_scores]
#     m = data['Название'].iloc[book_indices]
#     m.to_dict()
#     print(m)
#     return m


def address(message):
    global city
    city = message.text.lower()
    if message.text == 'макеевка':
        bot.send_message(message.chat.id, "В Макеевке есть два наших магазина!\n1) ТЦ «Центральный» 4-й эт.(ориентир маг. Золотой ключик) \n2) ТЦ Сигма- Ленд (бывший АШАН)")
    elif message.text == 'донецк':
        bot.send_message(message.chat.id, "Мы находимся в Донецке в ТЦ «Донецк Сити» 4-й эт.\n"
                                          "Магазин на 'Маяке' временно не работает")
    elif message.text == 'луганск':
        bot.send_message(message.chat.id, "Мы находимся в Луганске на ул. Оборонная, 9")
    bot.register_next_step_handler(message, send_text)


bot.polling(none_stop=True)
