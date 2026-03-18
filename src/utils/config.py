"""
Configuration utilities for AI Corp

Handles the separation between:
- Template: The reusable AI Corp system (templates/)
- Runtime: Project-specific operational state (.aicorp/)
"""

import os
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def get_template_path() -> Path:
    """
    Get the path to AI Corp templates.

    Checks in order:
    1. AI_CORP_TEMPLATE_PATH environment variable
    2. ./templates directory
    3. ../templates directory (for running from src/)
    4. Package installation location

    Returns:
        Path to the templates directory
    """
    env_path = os.environ.get('AI_CORP_TEMPLATE_PATH')
    if env_path:
        return Path(env_path)

    cwd = Path.cwd()

    # Check current directory
    if (cwd / 'templates').exists():
        return cwd / 'templates'

    # Check parent directory
    if (cwd.parent / 'templates').exists():
        return cwd.parent / 'templates'

    # Try to find relative to this file (for installed package)
    this_file = Path(__file__).resolve()
    package_root = this_file.parent.parent.parent
    if (package_root / 'templates').exists():
        return package_root / 'templates'

    raise FileNotFoundError(
        "Cannot find AI Corp templates. Set AI_CORP_TEMPLATE_PATH environment variable."
    )


def get_corp_path(project_path: Optional[Path] = None) -> Path:
    """
    Get the AI Corp runtime data path for a project.

    The runtime data lives in .aicorp/ within the project directory.

    Args:
        project_path: Path to the project. If None, uses current directory.

    Checks in order:
    1. AI_CORP_PATH environment variable (for backwards compatibility)
    2. project_path/.aicorp/
    3. ./.aicorp/

    Returns:
        Path to the .aicorp directory
    """
    # Backwards compatibility with AI_CORP_PATH
    env_path = os.environ.get('AI_CORP_PATH')
    if env_path:
        return Path(env_path)

    if project_path:
        return Path(project_path) / '.aicorp'

    cwd = Path.cwd()

    # Check for .aicorp in current directory
    if (cwd / '.aicorp').exists():
        return cwd / '.aicorp'

    # Default to .aicorp in current directory (will be created on init)
    return cwd / '.aicorp'


def init_project(
    project_path: Path,
    template: str = 'software',
    force: bool = False
) -> Path:
    """
    Initialize a new AI Corp project from a template.

    Creates the project directory structure with:
    - .aicorp/org/ - Copied from template
    - .aicorp/beads/ - Empty
    - .aicorp/hooks/ - Empty
    - etc.

    Args:
        project_path: Where to create the project
        template: Template name (e.g., 'software')
        force: Overwrite existing .aicorp directory if True

    Returns:
        Path to the .aicorp directory
    """
    project_path = Path(project_path).resolve()
    aicorp_path = project_path / '.aicorp'

    if aicorp_path.exists() and not force:
        raise FileExistsError(
            f"Project already initialized at {aicorp_path}. "
            "Use force=True to overwrite."
        )

    # Get template path
    templates_path = get_template_path()
    template_path = templates_path / template

    if not template_path.exists():
        available = [d.name for d in templates_path.iterdir() if d.is_dir()]
        raise FileNotFoundError(
            f"Template '{template}' not found. Available: {available}"
        )

    # Create project directory if needed
    project_path.mkdir(parents=True, exist_ok=True)

    # Remove existing .aicorp if force
    if aicorp_path.exists() and force:
        shutil.rmtree(aicorp_path)

    # Create .aicorp directory structure
    aicorp_path.mkdir(parents=True, exist_ok=True)

    # Copy org structure from template
    template_org = template_path / 'org'
    if template_org.exists():
        shutil.copytree(template_org, aicorp_path / 'org')

    # Create empty runtime directories
    runtime_dirs = ['beads', 'hooks', 'molecules', 'channels', 'gates', 'pools', 'memory']
    for dir_name in runtime_dirs:
        (aicorp_path / dir_name).mkdir(exist_ok=True)

    # Create molecules subdirectories
    (aicorp_path / 'molecules' / 'active').mkdir(exist_ok=True)
    (aicorp_path / 'molecules' / 'completed').mkdir(exist_ok=True)
    (aicorp_path / 'molecules' / 'templates').mkdir(exist_ok=True)

    # Create channel subdirectories
    (aicorp_path / 'channels' / 'downchain').mkdir(exist_ok=True)
    (aicorp_path / 'channels' / 'upchain').mkdir(exist_ok=True)
    (aicorp_path / 'channels' / 'peer').mkdir(exist_ok=True)
    (aicorp_path / 'channels' / 'broadcast').mkdir(exist_ok=True)

    # Create memory subdirectory
    (aicorp_path / 'memory' / 'organizational').mkdir(exist_ok=True)

    return aicorp_path


def load_config(config_name: str, corp_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load a configuration file from the corp/org directory.

    Args:
        config_name: Name of the config file (without .yaml)
        corp_path: Optional path to corp directory

    Returns:
        Configuration dictionary
    """
    if corp_path is None:
        corp_path = get_corp_path()

    config_file = corp_path / 'org' / f'{config_name}.yaml'

    if not config_file.exists():
        raise FileNotFoundError(f"Configuration not found: {config_file}")

    return yaml.safe_load(config_file.read_text())


def load_hierarchy(corp_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load the organizational hierarchy"""
    return load_config('hierarchy', corp_path)


def load_department(department_name: str, corp_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load a department configuration"""
    if corp_path is None:
        corp_path = get_corp_path()

    dept_file = corp_path / 'org' / 'departments' / f'{department_name}.yaml'

    if not dept_file.exists():
        raise FileNotFoundError(f"Department not found: {dept_file}")

    return yaml.safe_load(dept_file.read_text())


def load_roles(role_type: str, corp_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load role definitions"""
    if corp_path is None:
        corp_path = get_corp_path()

    role_file = corp_path / 'org' / 'roles' / f'{role_type}.yaml'

    if not role_file.exists():
        raise FileNotFoundError(f"Roles not found: {role_file}")

    return yaml.safe_load(role_file.read_text())


def get_role_by_id(role_id: str, corp_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Get a specific role by ID"""
    if corp_path is None:
        corp_path = get_corp_path()

    roles_dir = corp_path / 'org' / 'roles'

    for role_file in roles_dir.glob('*.yaml'):
        data = yaml.safe_load(role_file.read_text())
        for role in data.get('roles', []):
            if role.get('id') == role_id:
                return role

    return None


def list_templates() -> list[str]:
    """List available templates"""
    templates_path = get_template_path()
    return [d.name for d in templates_path.iterdir() if d.is_dir()]


def is_initialized(project_path: Optional[Path] = None) -> bool:
    """Check if a project is initialized with AI Corp"""
    corp_path = get_corp_path(project_path)
    return corp_path.exists() and (corp_path / 'org').exists()
