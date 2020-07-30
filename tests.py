from copy import deepcopy
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch, Mock

from PIL import Image
from pony.orm import db_session, rollback
from vk_api.bot_longpoll import VkBotMessageEvent
import settings
from Bot import Bot
from generate_ticket import drawing


def isolate_db(test_func):
    def wrapper(*args, **kwargs):
        with db_session():
            test_func(*args, **kwargs)
            rollback()

    return wrapper


class Test1(TestCase):
    RAW_EVENT = {
        'type': 'message_new',
        'object':
            {'message': {
                'date': 1587740080, 'from_id': 139905067, 'id': 133, 'out': 0, 'peer_id': 139905067,
                'text': 'Привет бот',
                'conversation_message_id': 114, 'fwd_messages': [], 'important': False, 'random_id': 0,
                'attachments': [],
                'is_hidden': False},
                'client_info': {'button_actions': ['text', 'vkpay', 'open_app', 'location', 'open_link'],
                                'keyboard': True, 'inline_keyboard': True, 'lang_id': 0}},
        'group_id': 194505054, 'event_id': 'f5c5ad8d81d75e52fd4af0b8dda39a9eeaf0a29c'}

    def test_run(self):
        count = 5
        obj = {'a': 1}
        events = [obj] * count
        long_poller_mock = Mock(return_value=events)
        long_poller_listen_mock = Mock()
        long_poller_listen_mock.listen = long_poller_mock

        with patch('Bot.vk_api.VkApi'):
            with patch('Bot.VkBotLongPoll', return_value=long_poller_listen_mock):
                bot = Bot('', '')
                bot.on_event = Mock()
                bot.send_image = Mock()
                bot.run()
                bot.on_event.assert_called()
                bot.on_event.assert_any_call(obj)
                assert bot.on_event.call_count == count

    INPUTS = [
        'Абра-кадабра',
        'здравствуй ботик',
        'Помоги пожалуйста',
        'заказ хочу сделать',
        'Мурманск',
        'Лондон',
        'москву',
        '19.07.2020',
        '3200',
        '3',
        'Надоели тесты',
        '88005553535',
        'Да',
    ]

    EXPECTED_OUTPUTS = [
        settings.DEFAULT_ANSWER,
        settings.INTENTS[0]['answer'],
        settings.INTENTS[1]['answer'],
        settings.SCENARIOS['registration']['steps']['step1']['text'],
        settings.SCENARIOS['registration']['steps']['step1']['failure_text'].format(dep_val_city=' Москва\n Лондон\n'),
        settings.SCENARIOS['registration']['steps']['step2']['text'],
        settings.SCENARIOS['registration']['steps']['step3']['text'],
        settings.SCENARIOS['registration']['steps']['step4']['text'].format(list_flight=' 28.07.2020 - 3200 - 15:00\n'
                                                                                        ' 28.07.2020 - 3201 - 14:00\n'
                                                                                        ' 28.07.2020 - 3202 - 13:00\n'
                                                                                        ' 28.07.2020 - 3203 - 12:00\n'
                                                                                        ' 28.07.2020 - 3204 - 11:00\n'),
        settings.SCENARIOS['registration']['steps']['step5']['text'],
        settings.SCENARIOS['registration']['steps']['step6']['text'],
        settings.SCENARIOS['registration']['steps']['step7']['text'],
        settings.SCENARIOS['registration']['steps']['step8']['text'].format(departure_city='Лондон',
                                                                            destination_city='Москва',
                                                                            departure_date='28.07.2020',
                                                                            num_flight='3200',
                                                                            num_seats='3',
                                                                            comment='Надоели тесты',
                                                                            phone_number='88005553535'),
        settings.SCENARIOS['registration']['steps']['step9']['text'].format(phone_number='88005553535'),
    ]

    @isolate_db
    def test_run_ok(self):
        send_mock = Mock()
        api_mock = Mock()
        api_mock.messages.send = send_mock
        events = []
        for input_text in self.INPUTS:
            event = deepcopy(self.RAW_EVENT)
            event['object']['message']['text'] = input_text
            events.append(VkBotMessageEvent(event))
        long_poller_mock = Mock()
        long_poller_mock.listen = Mock(return_value=events)

        with patch('Bot.VkBotLongPoll', return_value=long_poller_mock):
            bot = Bot(settings.GROUP_ID, settings.TOKEN)
            bot.api = api_mock
            bot.send_image = Mock()
            bot.run()
        assert send_mock.call_count == len(self.INPUTS)

        real_outputs = []
        for call in send_mock.call_args_list:
            args, kwargs = call
            real_outputs.append(kwargs['message'])
        assert real_outputs == self.EXPECTED_OUTPUTS

    def test_image_generation(self):
        with open('images/ticket_template.png', 'rb') as image:
            image_mock = Mock()
            image_mock.content = image.read()
        with patch('requests.get', return_value=image_mock):
            ticket_file = drawing(fio='Олег Шейнов', from_='Москва', to="Лондон", date="12.07.2020", time="15:00",
                                  landing_time="14:30", plane='D 1823', place='65A', row='40')
        with open('images/ticket_example.png', 'rb') as expected_file:
            expected_bytes = expected_file.read()
        assert ticket_file.read() == expected_bytes
