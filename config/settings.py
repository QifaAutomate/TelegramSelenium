from dataclasses import dataclass, field
from pathlib import Path
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

@dataclass
class ProjectConfig:
    project_name: str
    chat_name: str

    target_users: int = 200
    max_scroll_rounds: int = 350
    no_growth_limit: int = 8

    max_profiles: int = 50
    profile_no_growth_limit: int = 20

    chrome_profile: str = r"C:\papka"

    @property
    def output_dir(self) -> Path:
        path = DATA_DIR / "output" / self.project_name
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def input_dir(self) -> Path:
        return DATA_DIR / "input"

    @property
    def messages_file(self) -> Path:
        return self.output_dir / "messages.xlsx"

    @property
    def leads_file(self) -> Path:
        return self.output_dir / "leads.xlsx"

    @property
    def profiles_file(self) -> Path:
        return self.output_dir / "profiles_full.xlsx"