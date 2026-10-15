# Набор «Автомонтаж с Claude»

Рилс 1080×1920 одной командой: голос → сцены на весь экран → субтитры → звуки и музыка → обложка первым кадром.

## Что внутри
- `make.py` — вся сборка одной командой
- `script.json` — сценарий ролика (текст + какие сцены показывать). Его пишет Claude по запросу из урока 3
- `engine/reel.html` + `engine/scenes.js` — движок сцен (6 типов: hook, list, chat, code, number, cta)
- `voice/01.mp3 … 05.mp3` — пример голоса, чтобы первый запуск сработал сразу
- `music.mp3` — положи сюда свою фоновую музыку (без слов, с правом использования). Нет файла — соберётся без музыки

## Установка (один раз)
1. Python 3.10+ и ffmpeg:
   - Mac: `brew install python ffmpeg`
   - Windows: `winget install Python.Python.3.12` и `winget install Gyan.FFmpeg`
2. В папке набора:
```
pip install playwright
playwright install chromium
```
Проще всего — открыть папку в Claude Code и написать: «Установи всё, что нужно для make.py, и запусти пример».

## Запуск
```
python make.py script.json
```
Через 2–5 минут рядом появится `final.mp4` и `cover.png`.

## Голос
- Свой: запиши каждую фразу из `script.json` отдельным файлом `voice/01.mp3`, `02.mp3`… (в поле `voice.mode` — `own`)
- Нейросеть: `voice.mode` = `kie`, ключ kie.ai в переменной окружения `KIE_API_KEY`. Голос по умолчанию — Gacrux, скорость 1.15

## Типы сцен (поле `scene` у каждой фразы)
| scene | что показывает | поля |
|---|---|---|
| hook | крупный заголовок + карточки | title, sub, chips[], badge |
| list | окно со списком | num, title, tag, window, items[], pill |
| chat | чат: вопрос печатается, приходит ответ | num, title, window, prompt, answer, pill |
| code | терминал/код печатается | num, title, window, code, pill |
| number | большая цифра-счётчик | num, title, value, suffix, label |
| cta | кодовое слово в поле комментария | word, items[] |

Цвет всего ролика — `color`, у отдельной сцены — `color` внутри фразы.
Своя сцена: попроси Claude Code «добавь в engine/scenes.js новый тип сцены …» (урок 5).
