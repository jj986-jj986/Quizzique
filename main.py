from telebot import *
import openpyxl
import os
import csv
import random

funcs = 'Привет! Я — бот Quizik, способный помочь тебе выучить что-то важное :)\nСо мной ты можешь:\n/study - учить любую из доступных тем\n/info - узнать, как загрузить новый тест\n/upload - загрузить новый тест\n/stop - прекратить обучение и пойти отдохнуть'
tests_lst = []
tests = dict()
bloques = dict()
serv_lst = list()

API_TOKEN = '7094341055:AAFD8kBdZ3CPN0c1Hy2cHytk3PcqALoKqQE'
bot = telebot.TeleBot(token=API_TOKEN)


@bot.message_handler(commands=['help', 'start'])
def initial(message):
    ## Приветствие с возможными фукциями (add, study, change_block, stop)
    bot.send_message(message.chat.id, text=funcs)
    user_id = str(message.chat.id)
    with open('server.csv', 'r', encoding='utf8') as server:
        for line in server:
            line1 = line.strip()
            serv_lst.append(line1)
    for rec in serv_lst:
        if rec.startswith(user_id):
            return 0
    serv_lst.append(str(user_id + '//sillytest//'))
    with open('server.csv', 'w', encoding='utf8') as outfile:
        for rec in serv_lst:
            print(rec.strip(), file=outfile)
    file_name1 = user_id + 'sillytest_altered.csv'
    tests, bloques = alterer('sillytest.csv')
    with open(file_name1, 'w') as alterfile:
        for k, v in tests.items():
            print(k, v['ans'], '}+{'.join(v['opt']), v['got'], v['done'], v['per'], file=alterfile, sep=';')


@bot.message_handler(commands=['upload'])
def upload_file(message):
    bot.send_message(message.chat.id,
                     text="Пожалуйста, отправь мне файл в формате CSV\nЕсли необходима инструкция, можешь воспользоваться специальной командой:\n/info")


@bot.message_handler(commands=['info'])
def get_info(message):
    instruction = 'Чтобы загрузить новый тест, тебе нужно отправить мне файл в формате “.csv”, сделанный по шаблону ниже\nРядом с правильными ответами напиши “ - верно”. Не переживай, я буду предлагать варианты ответа в случайном порядке ;)\nЖду твоего файла!'
    with open('mock.csv', 'rb') as misc:
        bot.send_document(message.chat.id, misc, caption=instruction)


@bot.message_handler(content_types=['document'])
def handle_document(message):
    try:
        user_id = str(message.chat.id)
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_info = bot.get_file(file_id)
        # Скачивание файла
        downloaded_file = bot.download_file(file_info.file_path)
        file_name = str(file_name)
        src = os.path.join(message.document.file_name)
        with open(src, 'wb') as new_file:
            new_file.write(downloaded_file)
        tests, bloques = alterer(file_name)
        file_name1 = user_id + file_name[:-4] + '_altered.csv'
        with open(file_name1, 'w') as alterfile:
            for k, v in tests.items():
                print(k, v['ans'], '}+{'.join(v['opt']), v['got'], v['done'], v['per'], file=alterfile, sep=';')
        file_name2 = file_name[:-4] + '_blocks.csv'
        with open(file_name2, 'w') as outfile:
            for k, v in bloques.items():
                print(k, v, file=outfile, sep=' - ')
        server_writer(user_id, file_name[:-4])
        bot.send_message(message.chat.id, text="Файл успешно загружен!\n/study - учить его\n/upload - добавить новый")
    except:
        bot.send_message(message.chat.id, text='Ой, кажется произошла какая-то ошибка. Давай попробуем ещё раз?')
        pass


@bot.message_handler(commands=['study'])
def chose_study(message):
    user_id = str(message.chat.id)
    subjects = []
    bot.send_message(message.chat.id, text='Напиши название теста, который ты собираешься учить')
    with open('server.csv', 'r') as server:
        for line in server:
            if line.strip().startswith(user_id):
                line = line.split('//')
                subjects = line[1:]
                break
    n = len(subjects)
    printed = ''
    for t in range(n):
        if not subjects[t].isspace():
            printed += str(t + 1) + '. ' + subjects[t] + '\n'
    printed += 'Загрузить новый тест - /upload'
    ms = bot.send_message(message.from_user.id,
                          text=printed)
    bot.register_next_step_handler(message, chose_block)


def chose_block(message):
    if message.text == '/upload':
        upload_file(message)
        return 0
    bloques = []
    global quiz
    quiz = message.text.strip()
    topic = quiz + '_blocks.csv'
    try:
        with open(topic, 'r') as file:
            for line in file:
                bloques.append(line.strip())
        if not bloques:
            bot.register_next_step_handler(message, study)
        else:
            bot.send_message(message.chat.id, text='Выбери блок вопросов в данном тесте, написав его номер')
            text_bloques = str()
            for m in bloques:
                if not m.isspace():
                    text_bloques += m + '\n'
            message = bot.send_message(message.from_user.id, text=text_bloques)
            bot.register_next_step_handler(message, study)
    except:
        bot.send_message(message.chat.id, text='К сожалению, теста с таким именем нет :(\nСверь, верно ли введено имя?')
        bot.register_next_step_handler(message, chose_study)


def study(message):
    user_id = str(message.chat.id)
    global file_name_in
    file_name_in = user_id + quiz + '_altered.csv'
    tests = converter(file_name_in)
    result = message.text.split(' | ')
    bloo = result[0][:2]
    v = list(range(0, 4))
    questions = []
    for pergunta in tests.keys():
        if pergunta.startswith(bloo) and (tests[pergunta]['got'] < 3 or tests[pergunta]['per'] < 70):
            questions.append(pergunta)
    if len(questions) == 0:
        success_base = []
        for y in tests.values():
            z = y['got']
            if z != 0:
                success_base.append(y['per'])
        per = round(float(sum(success_base) / len(success_base)), 0)
        bot.send_message(message.chat.id,
                         text=f'Ура-ура, этот, блок пройден! Кстати, твой средний процент запоминаемости - {per}%, поздравляю!!\nВ этом разделе твои результаты будут сброшены на исходные - ты всегда можешь пройти его ещё раз')
        for x, y in tests.items():
            if x.startswith(bloo):
                y['got'] = 0
                y['per'] = 0
                y['done'] = 0
        deconverter(file_name_in, tests)
        return 0
        ## В список включаются вопросы, которые ещё не попадались или плохо запоминаются.
    quest = random.choice(questions)
    ## Достаётся случайный вопрос

    random.shuffle(v)
    ## Перемешиваются варианты ответов
    blocks_message = []
    for elem in v:
        writeithere = quest[:6] + ' | ' + tests[quest]['opt'][elem]
        blocks_message.append(writeithere.rstrip(';;'))

    keyboard = types.ReplyKeyboardMarkup(row_width=1)
    itembtn1 = types.KeyboardButton(blocks_message[0])
    itembtn2 = types.KeyboardButton(blocks_message[1])
    itembtn3 = types.KeyboardButton(blocks_message[2])
    itembtn4 = types.KeyboardButton(blocks_message[3])
    keyboard.add(itembtn1, itembtn2, itembtn3, itembtn4)
    # Кнопки с вариантами ответа
    ms = bot.send_message(message.from_user.id,
                          text=quest[6:].rstrip(';;'), reply_markup=keyboard)
    bot.register_next_step_handler(ms, callback_writer)


## Вывод: вопрос и варианты ответа, ввод вариант ответа - вызов следующей функции.
def callback_writer(call):
    tests = converter(file_name_in)
    if call.text == '/stop':
        stop(call)
        return 0
    if call.text == '/help':
        initial(call)
        return 0
    if call.text == '/study':
        chose_study(call)
        return 0
    if call.text == '/upload':
        upload_file(call)
        return 0
    # Возможность выйти из изучалки
    result = (call.text).split(' | ')
    valor = result[0][:6]
    checking = 'Ой! Здесь какая-то ошибка. Попробуй вызвать команду /study'
    for u in tests.keys():
        if u.startswith(valor):
            checking = tests[u]['ans']
            questionn = u
    if result[1].strip() == checking.strip():
        bot.send_message(call.chat.id, text='Всё верно!')
        tests[questionn]['done'] += 1
    else:
        bot.send_message(call.chat.id, text=f'К сожалению, неверно :(\nПравильный ответ: {checking}')
    tests[questionn]['got'] += 1
    zzz = tests[questionn]['got']
    z = tests[questionn]['done']
    if zzz != 0:
        tests[questionn]['per'] = round(float(z / zzz * 100), 1)
    deconverter(file_name_in, tests)
    study(call)


@bot.message_handler(commands=['stop'])
## стоп слово
def stop(message):
    tests = converter(file_name_in)
    success_base = []
    try:
        for y in tests.values():
            z = y['got']
            if z != 0:
                success_base.append(y['per'])
        per = round(float(sum(success_base) / len(success_base)), 0)
        bot.send_message(message.chat.id,
                                 text=f'Хорошая работа! Твой средний процент запоминаемости - {per}%, это кайф!\nКогда захочешь ещё поучиться, зови: /help',
                                 reply_markup=types.ReplyKeyboardRemove())
        return 0
    except:
        bot.send_message(message.chat.id,
                         text=f'Хорошая работа!\nКогда захочешь ещё поучиться, зови: /help',
                         reply_markup=types.ReplyKeyboardRemove())
        pass


def alterer(name):
    # Преобразует csv-файл в словарь на этапе загрузки
    tests = {}
    bloques = {}
    tests_lst = []
    with open(name, 'r', encoding='utf-8-sig') as file:
        ## преобразует csv в словарь
        for line in file:
            tests_lst.append(line.strip())
    block = 100
    num = 100
    for i in range(len(tests_lst)):
        elem = tests_lst[i]
        if "блок " in elem.lower():
            block += 10
            bloques[block] = elem  # создаёт словарь с блоками и присваивает каждому блоку уникальный номер
        if elem[1] == '.' or elem[2] == '.':
            num += 1
            question = elem
            while question[0].isalpha() != True:
                question = question[1:]
            question = str(block) + str(num) + ' ' + question
            t = i + 1
            options = []
            while tests_lst[t][1] == ')':  # определяет среди строк варианты ответа
                m = tests_lst[t][2:]
                if m.endswith('верно'):
                    m = m.strip('верно').strip(' -')
                    ans = m
                options.append(m.strip())
                t += 1
                if t == len(tests_lst):
                    break
            tests[question] = {'ans': ans, 'opt': options, 'got': 0, 'done': 0, 'per': 0}
    return tests, bloques


def server_writer(id, test):
    # создаёт в сервере запись о загрузке пользователем нового теста
    with open('server.csv', 'r', encoding='utf8') as server:
        serv_lst = []
        for line in server:
            if line.strip().startswith(id):
                line = line.strip() + test + '//'
            serv_lst.append(line)
    with open('server.csv', 'w', encoding='utf8') as outfile:
        for rec in serv_lst:
            print(rec, file=outfile)


def converter(name):
    # преобразует csv файл с тестом и данными конкретного пользователя в словарь
    with open(name, 'r') as infile:
        testy = {}
        for line in infile:
            record = line.strip().split(';')
            options = record[2].split('}+{')
            testy[record[0]] = {'ans': record[1], 'opt': options, 'got': int(record[3]), 'done': int(record[4]),
                                'per': float(record[5])}
    return testy


def deconverter(file_name, testy):
    # записывает результат изучения в csv файл
    with open(file_name, 'w', newline='') as alterfile:
        for k, v in testy.items():
            print(k, v['ans'], '}+{'.join(v['opt']), v['got'], v['done'], v['per'], file=alterfile, sep=';')


bot.polling(none_stop=True)
