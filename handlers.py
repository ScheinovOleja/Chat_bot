import re
from CITY_DICT import CITY_DICT
import generate_ticket as gt
import time
import datetime

re_phone = r'\d{,11}'
re_date = r'\d{2}.\d{2}.\d{4}'

search = {}


def flight_calculation(count, date, flight_str):
    for flight in CITY_DICT['cities'][search['departure_city']][search['destination_city']][date]:
        if count == 5:
            return flight_str, count
        count += 1
        flight_num = CITY_DICT['cities'][search['departure_city']][search['destination_city']][date][flight]
        flight_str = f'{flight_str} {date} - {flight_num} - {flight}\n'
    return flight_str, count


def dispatcher(text, context, user_date=None):
    flight_str = ''
    count = 0
    date = text
    while count < 5:
        try:
            flight_str, count = flight_calculation(count, date=date, flight_str=flight_str)
            day_old = date.split('.')[0]
            day_new = str(int(date.split('.')[0]) + 1)
            date = date.replace(day_old, day_new, 1)
        except KeyError:
            day_old = date.split('.')[0]
            day_new = str(int(date.split('.')[0]) + 1)
            date = date.replace(day_old, day_new, 1)
    return flight_str


def handle_departure_city(text, context, user_date=None):
    for dep_city in CITY_DICT['cities']:
        match = re.match(dep_city.split('/')[0], text)
        if match:
            search['departure_city'] = dep_city
            context['departure_city'] = dep_city.split('/')[1]
            return True
        else:
            continue
    flight_str = ''
    for dep_val_city in CITY_DICT['cities']:
        flight_str = f'{flight_str} {dep_val_city.split("/")[1]}\n'
    context['dep_val_city'] = flight_str
    return False


def handle_destination_city(text, context, user_date=None):
    for dest_city in CITY_DICT['cities'][search['departure_city']]:
        match = re.match(dest_city.split('/')[0], text)
        if match:
            search['destination_city'] = dest_city
            context['destination_city'] = dest_city.split('/')[1]
            return True
        else:
            continue
    flight_str = ''
    for dest_val_city in CITY_DICT['cities'][search['departure_city']]:
        flight_str = f'{flight_str} {dest_val_city.split("/")[1]}\n'
    context['dest_val_city'] = flight_str
    return False


def handle_departure_date(text, context, user_date=None):
    match = re.match(re_date, text)
    if match:
        user_date = time.gmtime(user_date)
        now_time = time.strftime('%d.%m.%Y', user_date)
        day_now = now_time.split('.')[0]
        month_now = now_time.split('.')[1]
        if text.split('.')[0] < day_now and text.split('.')[1] == month_now:
            context['fail_text'] = 'Сегодня во вчера смотреть нельзя! Повторите попытку'
            return False
        for dep_date in CITY_DICT['cities'][search['departure_city']][search['destination_city']]:
            if text == dep_date:
                context['departure_date'] = text
                context['list_flight'] = dispatcher(dep_date, context)
                return True
            else:
                context['list_flight'] = dispatcher(text, context)
                return True
    else:
        context['fail_text'] = 'Вы ввели неверную дату! Повторите попытку'
        return False


def handle_num_flight(text, context, user_date=None):
    for dep_city in CITY_DICT['cities']:
        for dest_city in CITY_DICT['cities'][dep_city]:
            for dep_date in CITY_DICT['cities'][dep_city][dest_city]:
                for dep_time in CITY_DICT['cities'][dep_city][dest_city][dep_date]:
                    if text == CITY_DICT['cities'][dep_city][dest_city][dep_date][dep_time]:
                        context['num_flight'] = text
                        context['time_flight'] = dep_time
                        landing_time = datetime.datetime.strptime(dep_time, "%H:%M") - datetime.timedelta(minutes=30)
                        context['landing_time'] = landing_time.strftime("%H:%M")
                        context['departure_date'] = dep_date
                        return True
    else:
        return False


def handle_num_seats(text, context, user_date=None):
    for let in text:
        if let.isdigit():
            if 6 > int(text) > 0:
                context['num_seats'] = text
                return True
            else:
                return False
        else:
            return False


def handle_comment(text, context, user_date=None):
    context['comment'] = text
    return True


def handle_answer(text, context, user_date=None):
    if text == 'да' or text == 'Да' or text == 'Верно':
        return True
    elif text == 'нет':
        return False


def handle_phone_number(text, context, user_date=None):
    match = re.match(re_phone, text)
    if len(text) != 11:
        return False
    if match:
        context['phone_number'] = match.group()
        return True
    else:
        return False


def generate_ticket_handle(text, context):
    return gt.make_ticket(
        fio=context['name'],
        from_=context['departure_city'],
        to=context['destination_city'],
        date=context['departure_date'],
        time=context['time_flight'],
        landing_time=context['landing_time']
    )
