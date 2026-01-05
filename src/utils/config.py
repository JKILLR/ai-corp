"""
Configuration utilities for AI Corp
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


def get_corp_path() -> Path:
    """
    Get the AI Corp base path.

    Checks in order:
    1. AI_CORP_PATH environment variable
    2. ./corp directory
    3. ../corp directory

    Returns:
        Path to the corp directory
    """
    env_path = os.environ.get('AI_CORP_PATH')
    if env_path:
        return Path(env_path)

    cwd = Path.cwd()

    # Check current directory
    if (cwd / 'corp').exists():
        return cwd / 'corp'

    # Check parent directory
    if (cwd.parent / 'corp').exists():
        return cwd.parent / 'corp'

    # Default to corp in current directory
    return cwd / 'corp'


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
