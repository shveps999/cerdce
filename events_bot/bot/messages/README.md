# Модуль сообщений бота

Этот модуль содержит все текстовые сообщения бота, структурированные по функциональности.

## Структура

```
messages/
├── __init__.py              # Экспорт всех классов сообщений
├── start_messages.py        # Сообщения для команды /start
├── user_messages.py         # Сообщения для пользовательских функций
├── post_messages.py         # Сообщения для создания/редактирования постов
├── feed_messages.py         # Сообщения для ленты событий
├── moderation_messages.py   # Сообщения для модерации
├── callback_messages.py     # Сообщения для callback запросов
├── notification_messages.py # Сообщения для уведомлений
├── common_messages.py       # Общие сообщения
└── README.md               # Эта документация
```

## Использование

### Импорт сообщений

```python
from events_bot.bot.messages import (
    StartMessages,
    UserMessages,
    PostMessages,
    FeedMessages,
    ModerationMessages,
    CallbackMessages,
    NotificationMessages,
    CommonMessages
)
```

### Пример использования

```python
from events_bot.bot.messages import StartMessages

@router.message(F.text == "/start")
async def cmd_start(message: Message):
    await message.answer(StartMessages.WELCOME)
```

## Классы сообщений

### StartMessages
Сообщения для обработчика команды `/start`:
- `WELCOME` - приветствие для новых пользователей
- `ALREADY_REGISTERED` - приветствие для зарегистрированных пользователей

### UserMessages
Сообщения для пользовательских функций:
- `REGISTRATION_SUCCESS` - успешная регистрация
- `SELECT_CATEGORIES` - выбор категорий
- `PROFILE_INFO` - информация о профиле
- `MY_POSTS_EMPTY` - нет постов у пользователя

### PostMessages
Сообщения для создания и редактирования постов:
- `CREATE_POST_START` - начало создания поста
- `ENTER_TITLE` - ввод заголовка
- `ENTER_CONTENT` - ввод содержания
- `ADD_PHOTO` - добавление фото
- `POST_CREATED` - пост создан успешно

### FeedMessages
Сообщения для ленты событий:
- `FEED_EMPTY` - лента пуста
- `POST_VIEW` - просмотр поста
- `LIKE_ADDED` - лайк добавлен
- `LIKE_REMOVED` - лайк удален

### ModerationMessages
Сообщения для модерации:
- `MODERATION_WELCOME` - приветствие в панели модерации
- `POST_APPROVED` - пост одобрен
- `POST_REJECTED` - пост отклонен
- `MODERATION_QUEUE_EMPTY` - очередь пуста

### CallbackMessages
Сообщения для callback запросов:
- `SELECT_AT_LEAST_ONE_CATEGORY` - выберите категорию
- `CATEGORIES_UPDATED` - категории обновлены
- `ACTION_SUCCESS` - действие выполнено

### NotificationMessages
Сообщения для уведомлений:
- `NEW_POST_NOTIFICATION` - новое событие
- `POST_APPROVED_NOTIFICATION` - пост одобрен
- `POST_REJECTED_NOTIFICATION` - пост отклонен

### CommonMessages
Общие сообщения:
- `ERROR_OCCURRED` - произошла ошибка
- `ACCESS_DENIED` - доступ запрещен
- `LOADING` - загрузка
- `HELP_GENERAL` - общая справка

## Преимущества структурирования

1. **Централизация** - все сообщения в одном месте
2. **Переиспользование** - одинаковые сообщения не дублируются
3. **Локализация** - легко добавить поддержку других языков
4. **Поддержка** - легко найти и изменить сообщения
5. **Консистентность** - единый стиль сообщений

## Добавление новых сообщений

1. Определите, к какому классу относится сообщение
2. Добавьте константу в соответствующий файл
3. Используйте в коде через импорт класса

## Форматирование

Сообщения поддерживают:
- Эмодзи для визуального оформления
- Переносы строк для структурирования
- Плейсхолдеры для динамических данных: `{variable}` 