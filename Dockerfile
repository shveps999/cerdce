# Используем официальный Python образ
FROM python:3.12-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем uv для управления зависимостями
RUN pip install uv

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости
RUN uv sync --frozen

# Копируем исходный код
COPY . .

VOLUME /app/uploads

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

RUN mkdir -p /app/uploads && \
    chown -R app:app /app/uploads && \
    chmod 755 /app/uploads
    
USER app

# Устанавливаем переменные окружения по умолчанию
ENV DATABASE_URL="sqlite+aiosqlite:///./events_bot.db"
ENV PYTHONPATH="/app"

# Открываем порт (если понадобится для веб-хуков)
EXPOSE 8080

# Команда запуска
CMD ["uv", "run", "python", "main.py"] 