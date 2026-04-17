# Telegram Parser Pipeline

Программа для автоматического сбора  лидов из Telegram-чатов с последующей загрузкой в amoCRM.

---

## Что делает программа

1. **Парсит сообщения** из Telegram-чата — собирает все сообщения участников
2. **Анализирует лидов** через GigaChat — определяет кто из участников является потенциальным клиентом
3. **Собирает профили** лидов — находит username и номер телефона каждого лида
4. **Загружает в amoCRM** — создаёт контакт и сделку для каждого лида

---

## Структура проекта

```
project/
├── config/
│   ├── .env              ← секретные ключи (заполняешь один раз)
│   └── settings.py       ← настройки проекта
├── core/
│   ├── browser.py        ← общие функции браузера
│   └── excel.py          ← общие функции работы с Excel
├── parsers/
│   ├── parser_messages.py   ← шаг 1: сбор сообщений
│   └── parser_profiles.py   ← шаг 3: сбор профилей
├── pipeline/
│   ├── analyze_leads.py     ← шаг 2: анализ лидов
│   └── amo_integration.py   ← шаг 4: загрузка в amoCRM
├── data/
│   ├── input/            ← сюда кладёшь входные Excel-файлы вручную
│   └── output/           ← сюда программа сохраняет результаты автоматически
├── orchestrator.py       ← управляет порядком шагов
└── run.py                ← точка входа, отсюда всё запускается
```

---

## Как работают данные между шагами

Каждый шаг создаёт файл, который использует следующий шаг:

```
Шаг 1: parser_messages   →  data/output/название_проекта/messages.xlsx
                                          ↓
Шаг 2: analyze_leads     →  data/output/название_проекта/leads.xlsx
                                          ↓
Шаг 3: parser_profiles   →  data/output/название_проекта/profiles_full.xlsx
                                          ↓
Шаг 4: amo_integration   →  amoCRM (контакты и сделки)
```

Все файлы одного проекта хранятся в своей папке и **никогда не пересекаются** с другими проектами.

---

## Установка и настройка (один раз)

### 1. Установи зависимости

```bash
pip install selenium openpyxl python-dotenv
```

### 2. Заполни файл `.env`

Открой файл `config/.env` и вставь свои ключи:

```
# GigaChat (для анализа лидов)
GIGACHAT_CREDENTIALS=твой_ключ_от_gigachat
GIGACHAT_SCOPE=GIGACHAT_API_B2B
GIGACHAT_MODEL=GigaChat-2-Pro

# amoCRM (для загрузки лидов)
AMO_SUBDOMAIN=твой_поддомен
AMO_CLIENT_ID=твой_client_id
AMO_CLIENT_SECRET=твой_secret
AMO_AUTH_CODE=твой_код_авторизации
AMO_REDIRECT_URI=https://example.com
```

> Если не знаешь где взять ключи — см. раздел "Где взять ключи" в конце документа.

### 3. Проверь путь к профилю Chrome

По умолчанию программа использует профиль Chrome по пути `C:\papka`.
Если у тебя другой путь — укажи его при запуске через `--chrome-profile`.

---

## Как запускать

### Базовый запуск — полный прогон всех 4 шагов

```bash
python run.py --project wb_partners --chat "WB Партнёры — чат"
```

Программа сама пройдёт все шаги по порядку и сохранит результаты в папку `data/output/wb_partners/`.

---

### Что такое `--project`

`--project` — это название папки, в которую сохранятся все результаты. Ты придумываешь его сама, любое слово без пробелов.

Папка создаётся **автоматически** при первом запуске — ничего руками делать не нужно.

Примеры:
```bash
--project wb_partners       →  data/output/wb_partners/
--project detskie_tovary    →  data/output/detskie_tovary/
--project ozon_april        →  data/output/ozon_april/
```

Один и тот же чат можно парсить сколько угодно раз под разными названиями проекта — результаты не перезапишутся:

```bash
python run.py --project wb_april --chat "WB Партнёры — чат"
python run.py --project wb_may  --chat "WB Партнёры — чат"
```

---

### Запустить только один шаг

Если предыдущие шаги уже отработали и нужно перезапустить только один:

```bash
# Только анализ лидов
python run.py --project wb_partners --chat "WB Партнёры — чат" --steps analyze

# Только сбор профилей
python run.py --project wb_partners --chat "WB Партнёры — чат" --steps profiles

# Только загрузка в amoCRM
python run.py --project wb_partners --chat "WB Партнёры — чат" --steps amo
```

---

### Запустить несколько шагов подряд

```bash
# Анализ и профили
python run.py --project wb_partners --chat "WB Партнёры — чат" --steps analyze profiles

# Профили и amoCRM
python run.py --project wb_partners --chat "WB Партнёры — чат" --steps profiles amo

# Анализ, профили и amoCRM (без первого шага — если сообщения уже собраны)
python run.py --project wb_partners --chat "WB Партнёры — чат" --steps analyze profiles amo
```

---

### Загрузить в amoCRM внешний Excel-файл (не из парсинга)

Если у тебя уже есть готовый список лидов в Excel и нужно просто загрузить его в amoCRM:

1. Положи файл в папку `data/input/`
2. Запусти:

```bash
python run.py --project detskie --chat "-" --steps amo --input "data/input/Детские одежда и товары Лиды 03.04.xlsx"
```

---

### Изменить количество пользователей и профилей

По умолчанию программа собирает 200 пользователей и парсит 50 профилей. Можно изменить:

```bash
python run.py --project wb_partners --chat "WB Партнёры — чат" --target-users 300 --max-profiles 100
```

---

### Указать другой путь к профилю Chrome

```bash
python run.py --project wb_partners --chat "WB Партнёры — чат" --chrome-profile "C:\Users\Ирина\chrome_profile"
```

---

## Все параметры запуска

| Параметр | Обязательный | По умолчанию | Описание |
|---|---|---|---|
| `--project` | Да | — | Название проекта (папка с результатами) |
| `--chat` | Да | — | Точное название чата в Telegram |
| `--steps` | Нет | все 4 шага | Какие шаги запустить |
| `--input` | Нет | — | Путь к внешнему Excel (только для шага amo) |
| `--target-users` | Нет | 200 | Сколько пользователей собрать |
| `--max-profiles` | Нет | 50 | Сколько профилей парсить |
| `--chrome-profile` | Нет | `C:\papka` | Путь к профилю Chrome |

---

## Примеры для разных сценариев

### Сценарий 1 — новый чат, полный прогон

```bash
python run.py --project ozon_sellers --chat "Озон Селлеры — чат"
```

### Сценарий 2 — упал шаг анализа, перезапустить с него

```bash
python run.py --project ozon_sellers --chat "Озон Селлеры — чат" --steps analyze profiles amo
```

### Сценарий 3 — собрать больше пользователей

```bash
python run.py --project wb_big --chat "WB Партнёры — чат" --target-users 500 --max-profiles 200
```

### Сценарий 4 — тот же чат, новый месяц

```bash
python run.py --project wb_may_2025 --chat "WB Партнёры — чат"
```

### Сценарий 5 — только загрузить готовый файл в amoCRM

```bash
python run.py --project detskie_april --chat "-" --steps amo --input "data/input/Детские одежда и товары Лиды 03.04.xlsx"
```

---

## Где хранятся результаты

После запуска в папке `data/output/название_проекта/` появятся файлы:

| Файл | Что содержит | Создаётся на шаге |
|---|---|---|
| `messages.xlsx` | Все участники чата и их сообщения | 1 — parser_messages |
| `leads.xlsx` | Только лиды с оценкой от 1 до 10 | 2 — analyze_leads |
| `profiles_full.xlsx` | Лиды с username и номером телефона | 3 — parser_profiles |

---

## Часто задаваемые вопросы

**Можно ли остановить программу и продолжить позже?**

Да. Программа сохраняет промежуточные результаты после каждого раунда скроллинга. Если остановить и перезапустить шаг — он начнёт заново, но данные предыдущего запуска останутся в файле.

**Что делать если шаг завершился с ошибкой?**

Запусти только упавший шаг через `--steps`. Например если упал шаг `analyze`:
```bash
python run.py --project wb_partners --chat "WB Партнёры — чат" --steps analyze
```

**Программа не находит чат — что делать?**

Проверь что название чата в `--chat` совпадает с названием в Telegram точь-в-точь, включая пробелы и тире. Лучше скопировать название прямо из Telegram.

**Можно ли запускать несколько проектов одновременно?**

Нет. Программа использует один браузер и одну сессию Telegram. Запускай проекты по очереди.

---

## Где взять ключи

### GigaChat

1. Зайди на [developers.sber.ru](https://developers.sber.ru)
2. Создай проект и получи `GIGACHAT_CREDENTIALS` (Base64-ключ)

### amoCRM

1. Зайди в amoCRM → Настройки → Интеграции → Создать интеграцию
2. Скопируй `CLIENT_ID` и `CLIENT_SECRET`
3. Получи `AUTH_CODE` через OAuth-авторизацию
4. `SUBDOMAIN` — это первая часть твоего адреса amoCRM (например если адрес `mycompany.amocrm.ru` то subdomain = `mycompany`)
