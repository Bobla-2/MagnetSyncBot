#!/bin/sh

if [ -z "$MODE" ]; then
    MODE=$(python -c "import config; print(config.UI_MODE)")
fi

if [ "$MODE" = "tg" ]; then
    echo "Starting TG bot"
    exec python main.py
else
    echo "Starting web (gunicorn)"
    exec gunicorn -w 1 --threads 4 -b 0.0.0.0:8000 flask_app:app
fi