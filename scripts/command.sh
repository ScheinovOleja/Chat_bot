# запуск тестов
python -m unittest

# coverage
coverage run -source=bot, handlers, settings -m unittest
coverage report -m

# создать базу PSQL
psql -c "create database chat_bot"
psql -d chat_bot