# UniversalShop — Telegram-магазин с админ-панелью

Готовый шаблон интернет-магазина в Telegram.  
Продавец управляет товарами, заказами, доставкой и настройками прямо в боте.

---

## 1. Что нужно для запуска

- **Токен бота** (получить у [@BotFather](https://t.me/BotFather)).
- **Ваш Telegram ID** (узнать у [@userinfobot](https://t.me/userinfobot)).
- **База данных PostgreSQL** (BotHost, Amvera, Supabase или локальный сервер).
- **Хостинг для бота** (рекомендуется BotHost или Amvera).

---

## 2. Установка (5 шагов)

### Шаг 1. Создайте бота
1. Откройте [@BotFather](https://t.me/BotFather) в Telegram.
2. Отправьте `/newbot`, придумайте имя и username.
3. Скопируйте **токен** (вида `1234567890:AAH...`).

### Шаг 2. Создайте базу данных
- Зарегистрируйтесь на [BotHost](https://bothost.ru) или [Amvera](https://amvera.ru).
- Создайте PostgreSQL базу.
- Скопируйте **строку подключения** (вида `postgresql://user:pass@host:port/db`).

### Шаг 3. Загрузите проект на хостинг
- Загрузите архив с проектом на ваш хостинг (BotHost поддерживает ZIP).
- Или загрузите код через Git (если хостинг поддерживает).

### Шаг 4. Добавьте переменные окружения
В панели хостинга найдите раздел **«Переменные»** (или «Environment Variables») и добавьте:

| Переменная | Значение |
|---|---|
| `BOT_TOKEN` | токен из BotFather |
| `ADMIN_ID` | ваш Telegram ID |
| `DATABASE_URL` | строка подключения к PostgreSQL (с префиксом `postgresql+asyncpg://`) |
| `DB_CONNECT_TIMEOUT` | `30` (опционально) |

**Пример `DATABASE_URL`:**