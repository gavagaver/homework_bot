import logging
import os
import sys
import time

import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

from exceptions import WrongAPIResponseCodeError

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PR_TOKEN')
TELEGRAM_TOKEN = os.getenv('TL_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s, %(name)s, %(levelname)s, %(message)s',
    level=logging.INFO
)


def check_tokens(*tokens):
    """Проверяет доступность переменных окружения."""
    return all(tokens)


def send_message(bot, message):
    """Отправляет сообщение в чат."""
    try:
        logging.info('Отправка сообщения начата')
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
    except telegram.TelegramError as error:
        logging.error(f'Сообщение не удалось отправить: {error}')
    else:
        logging.debug('Сообщение успешно отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к API."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    request_params = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    try:
        logging.info(
            (f'Начинаем подключение к эндпоинту {ENDPOINT}, с параметрами'
             f' headers = {HEADERS} ;params= {params}.')

        )
        response = requests.get(
            **request_params
        )
        if response.status_code != HTTPStatus.OK:
            raise WrongAPIResponseCodeError(
                'Ответ сервера не является успешным:'
                f' request params = {request_params};'
                f' http_code = {response.status_code};'
                f' reason = {response.reason}; content = {response.text}'
            )
        logging.info(f'Запрос к API выполнен. Ответ {response.status_code}')
        return response.json()
    except Exception as error:
        raise ConnectionError(
            (
                'Во время подключения к эндпоинту {url} произошла'
                ' непредвиденная ошибка: {error}'
                ' headers = {headers}; params = {params};'
            ).format(
                error=error,
                **request_params
            )
        )


def check_response(response):
    """Проверяет ответ API на соответствие документации."""
    try:
        timestamp = response['current_date']
    except KeyError:
        logging.error('Ключ current_date отсутствует в ответе API')
    try:
        homeworks = response['homeworks']
    except KeyError:
        logging.error('Ключ homeworks отсутствует в ответе API')
    if isinstance(timestamp, int) and isinstance(homeworks, list):
        return homeworks
    else:
        raise TypeError('Типы ключей current_date и homeworks не верны')


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is not None and homework_status is not None:
        if homework_status in HOMEWORK_VERDICTS:
            verdict = HOMEWORK_VERDICTS[homework_status]
            return (f'Изменился статус проверки работы '
                    f'"{homework_name}". {verdict}')
        else:
            raise ValueError('Статус работы не верен')
    else:
        raise ValueError('Информация не найдена')


def main():
    """Основная логика работы бота."""
    if not check_tokens(PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID):
        logging.critical('Токены не получены')
        sys.exit('Программа остановлена в связи с отсутствием токенов')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    while True:
        current_report = {'name': '', 'output': ''}
        prev_report = current_report.copy()
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = response.get('current_date', current_timestamp)
            homeworks = check_response(response)
            if homeworks:
                current_report['name'] = homeworks[0]['homework_name']
                current_report['output'] = parse_status(homeworks[0])
            else:
                current_report['output'] = (
                    f'За период от {current_timestamp} до настоящего момента'
                    ' домашних работ нет.'
                )
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy()
            else:
                logging.debug('В ответе нет новых статусов.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['output'] = message
            logging.error(message, exc_info=True)
            if current_report != prev_report:
                send_message(bot, current_report)
                prev_report = current_report.copy()
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        format=(
            '%(asctime)s [%(levelname)s] - '
            '(%(filename)s).%(funcName)s:%(lineno)d - %(message)s'
        ),
        level=logging.INFO,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    main()
