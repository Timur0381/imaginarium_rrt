import vk_api, json
from vk_api.longpoll import VkLongPoll, VkEventType
from config import token
from random import choice


class User:
    def __init__(self, id, score, mode, cards):
        self.id = id
        self.score = score
        self.mode = mode
        self.cards = cards

    def __str__(self):
        return f"{self.id=} {self.score=} {self.mode=}"


vk_session = vk_api.VkApi(token=token)
vk = vk_session.get_api()
longpoll = VkLongPoll(vk_session)
upload = vk_api.VkUpload(vk)


def get_keyboard(buttons):
    nb = []
    color = ''
    for i in range(len(buttons)):
        nb.append([])
        for k in range(len(buttons[i])):
            nb[i].append(None)
    for i in range(len(buttons)):
        for k in range(len(buttons[i])):
            text = buttons[i][k][0]
            color = {'зеленый': 'positive', 'красный': 'negative', 'синий': 'primary'}[buttons[i][k][1]]
            nb[i][k] = {"action": {"type": "text", "payload": "{\"button\": \"" + "1" + "\"}", "label": f"{text}"},
                        "color": f"{color}"}
    keyboard = {'one_time': True, 'buttons': nb}
    keyboard = json.dumps(keyboard, ensure_ascii=False).encode('utf-8')
    keyboard = str(keyboard.decode('utf-8'))
    return keyboard


def get_but(text, color):
    return {
        "action": {
            "type": "text",
            "payload": "{\"button\": \"" + "1" + "\"}",
            "label": f"{text}"
        },
        "color": f"{color}"
    }


def send_text(id, text):
    vk.messages.send(user_id=id, message=text, random_id=0)


def send_photo(id, url):
    vk.messages.send(user_id=id, attachment=url, random_id=0)


def send_common_word(id, cards: list):
    keywords = []
    used_words = []
    keywords_to_card = {key: [] for key in cards}
    rows = []
    with open("words.txt", "r") as words_file:
        lines = words_file.readlines()
        for card in cards:
            cur_row = lines[card - 1].split()
            rows.append(cur_row[1:])
            for i in range(1, len(cur_row)):
                if cur_row[i] in keywords:
                    keywords.remove(cur_row[i])
                    used_words.append(cur_row[i])
                elif cur_row[i] not in used_words:
                    keywords.append(cur_row[i])
    j = 0
    for i in range(len(keywords)):
        for j in range(5):
            if keywords[i] in rows[j]:
                keywords_to_card[cards[j]].append(keywords[i])
                break

    choosen_word = choice(keywords)
    vk.messages.send(user_id=id, message=choosen_word, random_id=0)

    return keywords_to_card, choosen_word


def send_cards(id):
    cards = []
    attachments = []
    if id in players_cards.keys():
        players_cards[id] = []
    for _ in range(5):
        card = choice(unused_cards)
        if id in players_cards.keys():
            players_cards[id].append(card)
        else:
            players_cards[id] = [card]
        used_cards.append(card)
        unused_cards.remove(card)
        photo = upload.photo_messages(f"images\\{card}.jpg")
        owner_id = photo[0]['owner_id']
        photo_id = photo[0]['id']
        access_key = photo[0]['access_key']
        attachment = f'photo{owner_id}_{photo_id}_{access_key}'
        cards.append(card)
        attachments.append(attachment)
    vk.messages.send(user_id=id, attachment=attachments, random_id=0)
    return cards



users = []
ids = []


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:
        if event.to_me:


            msg = event.text.lower()
            id = event.user_id
            
            if id not in ids:
                ids.append(id)
                users.append(User(id, 0, 'start', []))

            if msg == 'старт' or msg == 'дальше' or msg == 'начать':
                for user in users:
                    if user.id == id:
                        unused_cards = [i for i in range(1, 99)]
                        players_cards = {}
                        used_cards = []
                        cards = send_cards(id)
                        words_dict, word = send_common_word(id, cards)

                        for i in words_dict.keys():
                            if word in words_dict[i]:
                                correct_number = i
                                break

                        singleplayer_keyboard = get_keyboard([
                            [(cards[0], 'синий'), (cards[1], 'синий'), (cards[2], 'синий'), (cards[3], 'синий'),
                             (cards[4], 'синий')]
                        ])
                        vk_session.method('messages.send',
                                          {'user_id': id,
                                           'message': "Укажите номер карточки, которую описывает это слово",
                                           'random_id': 0,
                                           'keyboard': singleplayer_keyboard})
                        user.mode = 'choose'
                        user.cards = cards

            if msg == 'стоп':
                for user in users:
                    if user.id == id:
                        user.mode = 'start'
                        vk.messages.send(user_id=id,
                                         message=f'Ваш счет: {user.score}\nВы можете начать новую игру, написав "Старт"',
                                         random_id=0)
                        user.score = 0


            for user in users:
                if user.id == id:

                    if user.mode == 'choose':

                        if msg == str(correct_number):
                            user.score += 3
                            vk.messages.send(user_id=id,
                                             message=f'Вы ответили правильно\nВаш счет: {user.score}\nВы можете продолжить игру, написав "Дальше" или закончить ее, написав "Стоп"',
                                             random_id=0)
                            user.mode = "play"
                        elif msg.isdigit():
                            vk.messages.send(user_id=id,
                                             message=f'Вы ответили неверно\nВаш счет: {user.score}\nВы можете продолжить игру, написав "Дальше" или закончить ее, написав "Стоп"',
                                             random_id=0)
                            user.mode = "play"

