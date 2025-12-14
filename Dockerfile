# Используем multi-stage build
FROM python:3.10-slim as builder

# Создаем пользователя для безопасности
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Устанавливаем зависимости в отдельном слое
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Финальный образ
FROM python:3.10-slim

# Создаем того же пользователя
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Копируем только необходимые файлы
COPY --from=builder /root/.local /home/appuser/.local
COPY --chown=appuser:appuser . /app

# Устанавливаем PATH для пользователя
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

WORKDIR /app

# Переключаемся на непривилегированного пользователя
USER appuser

# Добавляем health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["python", "core/main.py"]
