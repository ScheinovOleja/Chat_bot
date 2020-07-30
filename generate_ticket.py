from io import BytesIO
import random
import string
import requests
from PIL import Image, ImageDraw, ImageFont

AVATAR_SIZE = 100


def drawing(fio, from_, to, date, time, landing_time, plane, place, row):
    font = ImageFont.truetype('Roboto/Roboto-regular.ttf', size=14)
    font_fatty = ImageFont.truetype('Roboto/Roboto-black.ttf', size=16)
    fill = 'White'
    img = Image.open('images\\ticket_template.png')
    modify = ImageDraw.Draw(img)
    modify.rectangle((40, 135, 235, 145), fill=fill)  # ФИО
    modify.rectangle((40, 200, 145, 215), fill=fill)  # откуда
    modify.rectangle((40, 270, 145, 280), fill=fill)  # куда
    modify.rectangle((280, 270, 325, 280), fill=fill)  # Дата
    modify.rectangle((390, 265, 430, 280), fill=fill)  # Время отправки
    modify.rectangle((395, 330, 445, 350), fill=fill)  # Время посадки
    modify.rectangle((45, 330, 100, 350), fill=fill)  # Самолет
    modify.rectangle((180, 330, 215, 350), fill=fill)  # Место
    modify.rectangle((290, 330, 315, 350), fill=fill)  # Ряд
    modify.text(xy=(45, 130), text=fio, font=font, fill='Black')  # ФИО
    modify.text(xy=(45, 200), text=from_, font=font, fill='Black')  # откуда
    modify.text(xy=(45, 265), text=to, font=font, fill='Black')  # куда
    modify.text(xy=(285, 265), text=date, font=font, fill='Black')  # Дата
    modify.text(xy=(395, 265), text=time, font=font, fill='Black')  # Время отправки
    modify.text(xy=(395, 330), text=landing_time, font=font_fatty, fill='Black')  # Время посадки
    modify.text(xy=(45, 330), text=plane, font=font_fatty, fill='Black')  # Самолет
    modify.text(xy=(180, 330), text=place, font=font_fatty, fill='Black')  # Место
    modify.text(xy=(290, 330), text=row, font=font_fatty, fill='Black')  # Ряд

    temp_file = BytesIO()
    response = requests.get(url=f'https://api.adorable.io/avatars/{AVATAR_SIZE}/{fio}')
    avatar_like = BytesIO(response.content)
    avatar = Image.open(avatar_like)
    img.paste(avatar, (450, 70))
    img.save(temp_file, 'png')
    temp_file.seek(0)
    return temp_file


def random_data():
    plane = random.choice(string.ascii_uppercase) + ' ' + str(random.randint(1000, 9999))
    place = str(random.randint(1, 1000)) + random.choice(string.ascii_uppercase)
    row = str(random.randint(1, 70))
    return plane, place, row


def make_ticket(fio, from_, to, date, time, landing_time):
    plane, place, row = random_data()
    return drawing(fio, from_, to, date, time, landing_time, plane, place, row)
