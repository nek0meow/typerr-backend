# Бекенд-часть для тренажёра скорости печати Typerr

Репозиторий состоит из ML-модуля на Python и Sprint Boot части для реализации эндпоинтов. Необходимые сервисы запускаются через docker compose.

## Как запускать
 
## 1. Определить файлы окружения в .env
```dotenv
DB_NAME=dbname
MLFLOW_DB_NAME=dbname_mlflow
DB_PASSWORD=password
DB_USER=user
DB_PORT=5432
```

При этом стоит поменять названия баз данных на соответствующие и в /init-db/create-multiple-dbs.sql

## 2. Запуск Postgres для работы сервера и MLflow

```powershell
docker compose up -d
```

После этого на клиент начнут приходить ответы.
При этом сервер MLflow запускается на `localhost:5000`, откуда будут подгружаться модели.

## 3. Создание модели
Модель использует недавние ошибки пользователя, чтобы построить TF-IDF эмбеддинг на триграммах непробельных символов. Она ранжирует по ним слова из `typerr_backend/src/main/resources/static/20k` по релевантности триграмм.

В директории ml создать окружение и установить зависимости:
```powershell
cd ..\ml
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Обучить модель на данных (Реализация опирается на датасет из `https://userinterfaces.aalto.fi/136Mkeystrokes/`). Пример данных показан в sample_file.txt.

```powershell
python .\train.py --data-dir "...\files\"
```
`--data-dir` принимает файл или директории файлов на подобии `sample_file.txt`. Может быть `.txt`, `.tsv` или `.csv`.

Опции:

```powershell
python .\train.py `
  --data-dir "C:\path\to\keystroke_logs" `
  --vocabulary-path "..\typerr_backend\src\main\resources\static\20k.txt" `
  --last-n 20 `
  --tracking-uri http://127.0.0.1:5000
```

Артефакты обучения:

- `artifacts/typing_recommender.joblib`
- `artifacts/user_error_profiles.csv`
- `artifacts/sample_recommendations.csv`
- `artifacts/model_info.json`

## 4. Inference

Можно делать запрос напрямую в виде массива слов:

```powershell
python .\predict.py --error-words "schedule thanks though" --top-k 20
```

Также можно собрать ошибки по логам пользователя:

```powershell
python .\predict.py `
  --data-dir "...\files\" `
  --participant-id 9989 `
  --last-n 20 `
  --top-k 20
```

Пример вывода:
```json
[
  {
    "word": "schedule",
    "score": 0.42,
    "frequency": 0.18,
    "matched_trigrams": "sch che hed edu dul ule"
  }
]
```

## 5. Взаимодействие с MLflow

Зарегистрированная в MLflow модель принимает:

- `error_words`: проблемные слова через пробел, дополнительно `top_k`
- `target` и `typed`, дополнительно `last_n` and `top_k`

Пример:

```json
{
  "dataframe_split": {
    "columns": ["target", "typed", "last_n", "top_k"],
    "data": [
      ["Please pass along my thanks, though.", "Please pass along my tanks, thogh.", 20, 20]
    ]
  }
}
```

## Особенности препроцессинга

- Особые символы принимаются за пробелы.
- Верхний регистр принимается за нижний. Используются только английские `a-z`
- Слова короче 3 букв игнорируются.