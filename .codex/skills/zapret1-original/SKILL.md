---
name: zapret1-original
description: "Используй, когда работа зависит от оригинальной семантики Zapret 1 / winws1 / nfqws: @config, --comment, отсутствие --name, hostlist/ipset, dpi-desync, dry-run или сверка ZapretGUI с G:\\Privacy\\zapret_orig_bolvan."
---

# Оригинальный Zapret 1

Используй этот skill перед изменениями кода, который читает, пишет, запускает или проверяет пресеты `winws1`.

## Где проверять

Источник правды по Запрету 1:

- Windows-путь: `G:\Privacy\zapret_orig_bolvan`
- WSL-путь: `/mnt/g/Privacy/zapret_orig_bolvan`
- Основная документация: `/mnt/g/Privacy/zapret_orig_bolvan/docs/readme.md`
- Основной разбор опций: `/mnt/g/Privacy/zapret_orig_bolvan/nfq/nfqws.c`

Перед тем как считать параметр поддержанным, проверь его в оригинале:

```bash
rg -n -- "--comment|--name|@<config_file>|config_from_file|wordexp|--dry-run|--hostlist|--ipset|--dpi-desync" \
  /mnt/g/Privacy/zapret_orig_bolvan/docs/readme.md \
  /mnt/g/Privacy/zapret_orig_bolvan/nfq/nfqws.c
```

## Имена профилей в ZapretGUI

В оригинальном Запрете 1 нет `--name` для имени профиля.

Для ZapretGUI имя профиля в `winws1` нужно хранить через:

```text
--comment=<имя профиля>
```

`--comment` в оригинальном Запрете 1 - это любой текст, который сам `winws1` игнорирует. Для GUI это удобное место, чтобы сохранить имя профиля, не ломая запуск.

Не добавляй `--name` в пресеты `winws1`, `@config` для `winws1`, пользовательские профили `winws1` и тестовые фикстуры `winws1`. `--name` относится к profile-синтаксису Запрета 2 / `winws2`.

## Запуск через @config

Оригинальный Запрет 1 поддерживает запуск через файл конфигурации:

```text
@<config_file>|$<config_file>
```

Эта опция должна быть первой. Остальные аргументы командной строки рядом с `@file` игнорируются, поэтому всё нужное для запуска должно быть внутри самого файла.

В `nfq/nfqws.c` чтение делает `config_from_file()`, затем используется `wordexp()`. Поэтому при генерации `@config` для `winws1` обязательно безопасно экранируй аргументы с пробелами, скобками и кириллицей.

## Проверка запуска

Если Запрет 1 не стартует, сначала смотри реальный текст `@config` и проверяй его установленным Windows-бинарником:

```bash
cmd.exe /c "cd /d C:\Zapret\Dev && exe\winws.exe @C:\Zapret\Dev\tmp\winws1_at_config\<file>.txt"
```

Для Windows-бинарника пути внутри `@config` должны быть Windows-путями вида `C:\Zapret\Dev\...`, а не WSL-путями `/mnt/c/...`.

## Граница с Zapret 2

Не переносить правила `winws2` в `winws1` автоматически.

Особенно важно:

- `winws1`: имя GUI-профиля через `--comment`;
- `winws2`: имя profile через `--name`;
- `winws1`: проверять параметры по `/mnt/g/Privacy/zapret_orig_bolvan`;
- `winws2`: проверять параметры по `/mnt/g/Privacy/zapret2_orig_bolvan`.
