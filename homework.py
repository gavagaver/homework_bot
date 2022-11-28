import logging
import os
import time

import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

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

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s, %(levelname)s, %(message)s'
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)


def check_tokens(*tokens):
    """Проверяет доступность переменных окружения"""
    if not all([token in os.environ for token in tokens]):
        logger.error('Ошибка импорта токенов')
        return False
    return True


def send_message(bot, message):
    """Отправляет сообщение в чат"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception as error:
        logger.error(f'Ошибка при обращении к API: {error}')
    else:
        logger.debug('Сообщение успешно отправлено')


def get_api_answer(timestamp):
    """Делает запрос к API"""
    params = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    except Exception as error:
        raise SystemError(f'Ошибка выполнения запроса: {error}')
    content = response.json()
    if response.status_code == HTTPStatus.OK:
        return content
    else:
        raise SystemError(
            f'Ошибка при запросе к API: {content.get("message")}'
        )


def check_response(response):
    """Проверяет ответ API на соответствие документации"""
    try:
        timestamp = response['current_date']
    except KeyError:
        logger.error('Ключ current_date отсутствует в ответе API')
    try:
        homeworks = response['homeworks']
    except KeyError:
        logger.error('Ключ homeworks отсутствует в ответе API')
    if isinstance(timestamp, int) and isinstance(homeworks, list):
        return homeworks
    else:
        raise TypeError('Типы ключей current_date и homeworks не верны')


def parse_status(homework):
    """Извлекает статус домашней работы"""
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_name is not None and homework_status is not None:
        if homework_status in HOMEWORK_VERDICTS:
            verdict = HOMEWORK_VERDICTS[homework_status]
            return (f'Изменился статус проверки работы '
                    f'"{homework_name}". {verdict}')
        else:
            raise SystemError('Статус работы не верен')
    else:
        raise SystemError('Информация не найдена')


def main():
    """Основная логика работы бота."""
    if check_tokens('PR_TOKEN', 'TL_TOKEN', 'CHAT_ID') is False:
        logger.critical('Токены не получены')
        return 0

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(timestamp)
            homeworks = check_response(response)
            if len(homeworks) > 0:
                message = parse_status(homeworks[0])
                send_message(bot, message)
            timestamp = int(time.time())
            time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
