# Homework bot - telegram-бот для Яндекс.Практикум
Телеграм-бот для уведомления о проверке домашней работы на Яндекс.Практикум.

## Описание

Телеграм-бот, работающий с API Яндекс.Практикума.  
Каждые 10 минут бот обращается к API.  
Когда статус проверки домашней работы изменен, бот присылает пользователю сообщение.  

## Установка и запуск
1. [ ] Клонировать репозиторий и перейти в него в командной строке:

```bash
git clone https://github.com/gavagaver/homework_bot.git && cd homework_bot
```

1. [ ] Создать и активировать виртуальное окружение:

###### Windows:
```bash
python -m venv venv
```
```bash
source venv/Scripts/activate
```
```bash
python -m pip install --upgrade pip
```
###### Linux:
```bash
python3 -m venv venv
```
```bash
source venv/bin/activate
```
```bash
python3 -m pip install --upgrade pip
```

1. [ ] Установить зависимости
```bash
pip install -r requirements.txt
``` 

1. [ ] Создать файл со следующими переменными:
```
PR_TOKEN - токен Яндекс.Практикума
TL_TOKEN - токен Telegram-бота
CHAT_ID - id пользователя
``` 

## Стек
- Python 3.7
- python-dotenv 0.19.0
- python-telegram-bot 13.7

## Об авторе
Голишевский Андрей Вячеславович  
Python-разработчик (Backend)  
E-mail: gav@gaver.ru  
Telegram: @gavagaver  
Россия, г. Москва  
