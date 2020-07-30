import requests
import vk_api
from pony.orm import db_session
from vk_api.bot_longpoll import VkBotLongPoll, VkBotEventType
import random
import logging
import handlers
from models import UserState, Registration

try:
    import settings
except ImportError:
    exit('Do cp Settings.py.default Settings.py and set token')

log = logging.getLogger('Bot')


def configure_logging():
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
    file_handler = logging.FileHandler('bot.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt='%d-%m-%Y %H:%M'))
    log.addHandler(stream_handler)
    log.addHandler(file_handler)
    log.setLevel(logging.DEBUG)


class Bot:
    """
    Сценарий регистрации пользователей на конференции через Vk.com
    Use python 3.8

    Поддерживает ответы на вопросы про дату, место проведения и сценарий регистрации:
    - спрашивает имя
    - спрашивает email
    - говорим об успешной регистрации
    Если шаг не пройден, задаем уточняющий вопрос пока шаг не будет пройден.
    """

    def __init__(self, group_id, token):
        """

        :param group_id: id группы
        :param token: секретный токен из той же группы
        """
        self.group_id = group_id
        self.token = token

        self.vk = vk_api.VkApi(token=self.token)
        self.long_poller = VkBotLongPoll(self.vk, self.group_id)

        self.api = self.vk.get_api()

        self.user_time = None

        self.name = str

    def run(self):
        """Запуск бота"""
        for events in self.long_poller.listen():
            try:
                self.on_event(events)
            except Exception as exc:
                log.debug(f"Ошибка в обработке события - {exc}")

    @db_session
    def on_event(self, event: VkBotEventType):
        """
        Обработка входящего события и отправка встречного сообщения
        """
        user_id = str(event.message.peer_id)
        text = event.message.text
        state = UserState.get(user_id=user_id)
        self.user_time = event.message.date
        user = self.vk.method("users.get", {"user_ids": user_id})
        self.name = user[0]['first_name'] + ' ' + user[0]['last_name']
        if state is not None:
            # продолжать сценарий
            self.continue_scenario(text=text, state=state, user_id=user_id)
        else:
            for intent in settings.INTENTS:
                if any(token in text.lower() for token in intent['tokens']):
                    # run intent
                    log.debug(f'Пользователь получил {intent}')
                    if intent['answer']:
                        self.send_text(intent['answer'], user_id)
                    else:
                        self.start_scenario(intent['scenario'], user_id, text)
                    break
            else:
                self.send_text(settings.DEFAULT_ANSWER, user_id)

    def send_text(self, text_to_send, user_id):
        self.api.messages.send(
            message=text_to_send,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_image(self, image, user_id):
        upload_url = self.api.photos.getMessagesUploadServer()['upload_url']
        upload_data = requests.post(url=upload_url, files={'photo': ('image.png', image, 'image/png')}).json()
        image_data = self.api.photos.saveMessagesPhoto(**upload_data)

        owner_id = image_data[0]['owner_id']
        media_id = image_data[0]['id']
        attachment = f"photo{owner_id}_{media_id}"

        self.api.messages.send(
            attachment=attachment,
            random_id=random.randint(0, 2 ** 20),
            peer_id=user_id,
        )

    def send_step(self, step, user_id, text, context):
        if 'text' in step:
            self.send_text(step['text'].format(**context), user_id)
        if 'image' in step:
            handler = getattr(handlers, step['image'])
            context['name'] = self.name
            image = handler(text, context)
            self.send_image(image, user_id)

    def start_scenario(self, scenario_name, user_id, text):
        scenario = settings.SCENARIOS[scenario_name]
        first_step = scenario['first_step']
        step = scenario['steps'][first_step]
        self.send_step(step, user_id, text, context={})
        UserState(user_id=user_id, scenario_name=scenario_name, step_name=first_step, context={})

    def continue_scenario(self, text, state, user_id):
        steps = settings.SCENARIOS[state.scenario_name]['steps']
        step = steps[state.step_name]
        handler = getattr(handlers, step['handler'])
        if handler(text=text, context=state.context, user_date=self.user_time):
            # next step
            next_step = steps[step['next_step']]
            self.send_step(next_step, user_id, text, state.context)
            if next_step['next_step']:
                # switch next step
                state.step_name = step['next_step']
            else:
                # finish scenario
                state.delete()
                log.info('Город отправления - {departure_city}\n'
                         'Город назначения - {destination_city}\n'
                         'Дата отправления - {departure_date}\n'
                         'Выбранный рейс - {num_flight}\n'
                         'Количество мест - {num_seats}\n'
                         'Комментарий к заказу:\n'
                         '{comment}\n'.format(**state.context))
                Registration(
                    name=self.name,
                    departure_city=state.context['departure_city'],
                    destination_city=state.context['destination_city'],
                    departure_date=state.context['departure_date'],
                    num_flight=state.context['num_flight'],
                    num_seats=state.context['num_seats'],
                    comment=state.context['comment'],
                    phone_number=state.context['phone_number'],
                )
        else:
            # retry current step
            text_to_send = step['failure_text'].format(**state.context)
            self.send_text(text_to_send, user_id)


if __name__ == '__main__':
    configure_logging()
    bot = Bot(group_id=settings.GROUP_ID, token=settings.TOKEN)
    bot.run()
