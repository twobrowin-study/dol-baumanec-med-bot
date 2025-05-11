# Расширение бота Google таблиц для поддержки функциональности мед осмотра

## Функциональное наполнение доступно в описании основной библиотеки [Spread Sheet Bot](https://github.com/twobrowin-study/spreadsheetbot-lib)

## Запуск приложения

`eval $(tr "\n" "\t" < env) python main.py` в директории `python`

Для запуска в режиме отладки могут использоваться флаги `debug`, `--debug`, `-D`.

## Сборка Docker контейнера

`docker build -t twobrowin/spreadsheet-bot:latest .`

`docker push twobrowin/spreadsheet-bot:latest`

## Запуск в Kubernetes

`helm upgrade --install --debug -n baumanec dol-baumanec-med-bot-2025 ./charts`

Требуются создать секрет `dol-baumanec-med-bot-2025` в неймспейсе `baumanec`

## Переменные окружения для запуска приложения

* `BOT_TOKEN` - токен подключения к Telegram боту

* `SHEETS_ACC_JSON` - JWT токен подключения к Google Spreadsheet API

* `SHEETS_LINK` - Ссылка на подключение к требуемой таблице - боту требуется доступ на запись, может быть передан как в ссылке, так и назначен инстрементами Google Spreadsheet

* `SWITCH_UPDATE_TIME` - Время обновления стандартной таблицы 

* `SETTINGS_UPDATE_TIME` - Время обновления стандартной таблицы 