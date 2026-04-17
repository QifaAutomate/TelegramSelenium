from pathlib import Path
from config.settings import ProjectConfig
from parsers.parser_messages import parse_messages
from parsers.parser_profiles import parse_profiles
from pipeline.analyze_leads import analyze_leads
from pipeline.amo_integration import push_to_amo

STEPS = ["messages", "analyze", "profiles", "amo"]

def run_pipeline(config: ProjectConfig, steps: list[str] = None, input_file: Path = None):
    steps = steps or STEPS

    invalid = [s for s in steps if s not in STEPS]
    if invalid:
        print(f"Неизвестные шаги: {invalid}. Доступные: {STEPS}")
        return

    print(f"  Проект: {config.project_name}")
    print(f"  Чат: {config.chat_name}")
    print(f"  Шаги: {steps}")

    if "messages" in steps:
        print("\nШАГ 1: Парсинг сообщений")
        parse_messages(config)

    if "analyze" in steps:
        print("\nШАГ 2: Анализ лидов")
        analyze_leads(config)

    if "profiles" in steps:
        print("\nШАГ 3: Парсинг профилей")
        parse_profiles(config)

    if "amo" in steps:
        print("\nШАГ 4: Загрузка в amoCRM")
        push_to_amo(config, input_file=input_file)

    print(f"Готово! Проект: {config.project_name}")
    print(f"Результаты: data/output/{config.project_name}/")