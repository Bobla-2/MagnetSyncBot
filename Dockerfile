# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем переменные окружения для корректной работы Python
ENV PYTHONDONTWRITEBYTECODE=1

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Копируем файл зависимостей
COPY ./requirements.txt /app/

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем файлы проекта в контейнер
COPY . /app/

# Открываем необходимые порты
EXPOSE 8080 9091 10809

RUN chmod +x /app/entrypoint.sh

CMD ["./entrypoint.sh"]