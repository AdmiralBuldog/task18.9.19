import logging
import requests
import telebot
from telebot import types

import config

TOKEN = config.TOKEN
API_KEY = config.API_KEY

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class APIException(Exception):
    pass


class CryptoCurrencyBot:
    def __init__(self, token):
        self.bot = telebot.TeleBot(token)
        self.cache = {'cryptos': []}
        self.selected_crypto = None
        self._setup_handlers()

    def get_cryptos_from_api(self):
        if self.cache['cryptos']:
            return self.cache['cryptos']
        base_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': API_KEY,
        }
        response = requests.get(base_url, headers=headers)
        data = response.json()
        data = data['data'][:10]
        excluded_cryptos = ['Tether USDt', 'USD Coin', 'TRON']
        cryptos = [crypto for crypto in data if crypto['name'] not in excluded_cryptos]
        self.cache['cryptos'] = cryptos
        return cryptos

    def _setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.start_over(message)

        @self.bot.message_handler(commands=['help'])
        def help_command(message):
            help_text = """
            Добро пожаловать в CryptoCurrencyBot!
            Вот что я могу делать:
            - Конвертировать криптовалюты в другие валюты.
            - Команда /start: начинает новую сессию конвертации.
            - Команда /help: показывает это сообщение.
            """
            self.bot.send_message(message.chat.id, help_text)

        @self.bot.callback_query_handler(func=lambda call: True)
        def callback_inline(call):
            if call.data in [crypto['symbol'] for crypto in self.get_cryptos_from_api()]:
                self.handle_crypto_selection(call)
            elif call.data in ['usd', 'eur', 'rub']:
                self.handle_currency_selection(call)
            elif call.data == 'restart':
                self.start_over(call.message)

    def start_over(self, message):
        markup = types.InlineKeyboardMarkup()
        cryptos = self.get_cryptos_from_api()
        for crypto in cryptos:
            markup.add(types.InlineKeyboardButton(text=crypto['name'], callback_data=crypto['symbol']))
        self.bot.send_message(message.chat.id, "Выберите криптовалюту:", reply_markup=markup)

    def handle_crypto_selection(self, call):
        self.selected_crypto = call.data
        new_text = "Выберите валюту:"
        markup = types.InlineKeyboardMarkup()
        for currency in ['usd', 'eur', 'rub']:
            markup.add(types.InlineKeyboardButton(text=currency.upper(), callback_data=currency))
        self.bot.edit_message_text(chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   text=new_text, reply_markup=markup)

    def handle_currency_selection(self, call):
        new_text = "Введите количество криптовалюты:"
        self.bot.edit_message_text(chat_id=call.message.chat.id,
                                   message_id=call.message.message_id,
                                   text=new_text)
        self.bot.register_next_step_handler(call.message, self.convert, call.data)

    def convert(self, message, currency):
        try:
            amount = float(message.text)
            rate = self.get_currency_rate(self.selected_crypto, currency)
            if rate is None:
                raise APIException(f'Не удалось найти информацию о {self.selected_crypto}.')
            converted_amount = round(amount * rate, 3)
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(text='Конвертировать ещё', callback_data='restart'))
            self.bot.send_message(message.chat.id,
                                  f'Если вы конвертируете {amount} {self.selected_crypto} в {currency.upper()}, вы '
                                  f'получите {converted_amount}.', reply_markup=markup)
        except APIException as e:
            self.bot.send_message(message.chat.id, f'Ошибка: {e}')
        except Exception as e:
            self.bot.send_message(message.chat.id, f'Ошибка при получении данных от API: {e}')

    def get_currency_rate(self, crypto_currency, target_currency):
        key = '{0}'.format(crypto_currency)
        if key not in self.cache:
            base_url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': API_KEY,
            }
            parameters = {
                'symbol': key,
                'convert': target_currency.upper()
            }
            response = requests.get(base_url, headers=headers, params=parameters)
            data = response.json()
            self.cache[key] = data['data'][key]['quote'][target_currency.upper()]['price']
        return self.cache[key]

    def run(self):
        self.bot.polling(none_stop=True)


if __name__ == '__main__':
    bot = CryptoCurrencyBot(TOKEN)
    bot.run()
