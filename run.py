import argparse
from pathlib import Path
from config.settings import ProjectConfig
from orchestrator import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Telegram Parser Pipeline")

    parser.add_argument("--project", required=True, help="Название проекта (папка в data/output/)")
    parser.add_argument("--chat", required=True, help="Название чата в Telegram")
    parser.add_argument(
        "--steps",
        nargs="+",
        choices=["messages", "analyze", "profiles", "amo"],
        default=["messages", "analyze", "profiles", "amo"],
        help="Шаги для выполнения"
    )
    parser.add_argument("--input", help="Путь к входному Excel (только для шага amo, если файл внешний)")
    parser.add_argument("--target-users", type=int, default=200, help="Сколько пользователей собрать (default: 200)")
    parser.add_argument("--max-profiles", type=int, default=50, help="Сколько профилей парсить (default: 50)")
    parser.add_argument("--chrome-profile", default=r"C:\papka", help="Путь к профилю Chrome")

    args = parser.parse_args()

    config = ProjectConfig(
        project_name=args.project,
        chat_name=args.chat,
        target_users=args.target_users,
        max_profiles=args.max_profiles,
        chrome_profile=args.chrome_profile,
    )

    input_file = Path(args.input) if args.input else None

    run_pipeline(config, steps=args.steps, input_file=input_file)


if __name__ == "__main__":
    main()