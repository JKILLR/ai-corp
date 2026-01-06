"""
AI Corp Preset System

Handles loading and applying industry presets for AI Corp deployments.
Presets define organizational structure, workflows, gates, and configuration
for specific industries or use cases.
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import yaml


@dataclass
class PresetMetadata:
    """Metadata about a preset"""
    id: str
    name: str
    description: str
    industry: str
    version: str = "1.0"
    author: str = "AI Corp"
    tags: List[str] = field(default_factory=list)
    complexity: int = 1
    team_size_min: int = 1
    team_size_max: int = 10
    team_size_default: int = 5


@dataclass
class PresetConfig:
    """Complete preset configuration"""
    metadata: PresetMetadata
    path: Path
    includes: Dict[str, Any] = field(default_factory=dict)
    customization: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, Any] = field(default_factory=dict)
    hooks: Dict[str, Any] = field(default_factory=dict)


class PresetManager:
    """
    Manages AI Corp presets.

    Presets are located in templates/presets/{preset-id}/
    """

    def __init__(self, templates_path: Optional[Path] = None):
        """
        Initialize the preset manager.

        Args:
            templates_path: Path to templates directory. If None, auto-detected.
        """
        if templates_path is None:
            templates_path = self._find_templates_path()

        self.templates_path = templates_path
        self.presets_path = templates_path / 'presets'

    def _find_templates_path(self) -> Path:
        """Find the templates directory"""
        import os

        # Check environment variable
        env_path = os.environ.get('AI_CORP_TEMPLATE_PATH')
        if env_path:
            return Path(env_path)

        # Check relative to this file
        this_file = Path(__file__).resolve()
        package_root = this_file.parent.parent.parent

        if (package_root / 'templates').exists():
            return package_root / 'templates'

        # Check current directory
        cwd = Path.cwd()
        if (cwd / 'templates').exists():
            return cwd / 'templates'

        raise FileNotFoundError(
            "Cannot find AI Corp templates. Set AI_CORP_TEMPLATE_PATH environment variable."
        )

    def list_presets(self) -> List[PresetMetadata]:
        """
        List all available presets.

        Returns:
            List of preset metadata objects
        """
        presets = []

        if not self.presets_path.exists():
            return presets

        for preset_dir in self.presets_path.iterdir():
            if not preset_dir.is_dir():
                continue

            # Skip hidden directories and _blank template in listings
            if preset_dir.name.startswith('.'):
                continue

            preset_file = preset_dir / 'preset.yaml'
            if preset_file.exists():
                try:
                    metadata = self._load_preset_metadata(preset_file)
                    presets.append(metadata)
                except Exception:
                    # Skip invalid presets
                    pass

        return presets

    def _load_preset_metadata(self, preset_file: Path) -> PresetMetadata:
        """Load preset metadata from preset.yaml"""
        data = yaml.safe_load(preset_file.read_text())

        metadata = data.get('metadata', {})
        team_size = metadata.get('team_size', {})

        return PresetMetadata(
            id=data.get('id', preset_file.parent.name),
            name=data.get('name', 'Unknown'),
            description=data.get('description', ''),
            industry=metadata.get('industry', 'generic'),
            version=data.get('version', '1.0'),
            author=metadata.get('author', 'Unknown'),
            tags=metadata.get('tags', []),
            complexity=metadata.get('complexity', 1),
            team_size_min=team_size.get('min', 1),
            team_size_max=team_size.get('max', 10),
            team_size_default=team_size.get('default', 5)
        )

    def get_preset(self, preset_id: str) -> Optional[PresetConfig]:
        """
        Get a preset by ID.

        Args:
            preset_id: The preset identifier

        Returns:
            PresetConfig if found, None otherwise
        """
        preset_path = self.presets_path / preset_id
        preset_file = preset_path / 'preset.yaml'

        if not preset_file.exists():
            return None

        data = yaml.safe_load(preset_file.read_text())
        metadata = self._load_preset_metadata(preset_file)

        return PresetConfig(
            metadata=metadata,
            path=preset_path,
            includes=data.get('includes', {}),
            customization=data.get('customization', {}),
            dependencies=data.get('dependencies', {}),
            hooks=data.get('hooks', {})
        )

    def apply_preset(
        self,
        preset_id: str,
        target_path: Path,
        name: Optional[str] = None,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Path:
        """
        Apply a preset to initialize a new AI Corp instance.

        Args:
            preset_id: The preset to apply
            target_path: Where to create the .aicorp directory
            name: Custom name for this corp instance
            customizations: Optional customization overrides

        Returns:
            Path to the created .aicorp directory
        """
        preset = self.get_preset(preset_id)
        if not preset:
            available = [p.id for p in self.list_presets()]
            raise ValueError(
                f"Preset '{preset_id}' not found. Available: {available}"
            )

        target_path = Path(target_path).resolve()
        aicorp_path = target_path / '.aicorp'

        # Create directory structure
        target_path.mkdir(parents=True, exist_ok=True)
        aicorp_path.mkdir(parents=True, exist_ok=True)

        # Copy org structure
        self._copy_org(preset, aicorp_path)

        # Copy workflows
        self._copy_workflows(preset, aicorp_path)

        # Copy skills
        self._copy_skills(preset, aicorp_path)

        # Copy gates
        self._copy_gates(preset, aicorp_path)

        # Copy and customize config
        self._copy_config(preset, aicorp_path, name, customizations)

        # Create runtime directories
        self._create_runtime_dirs(aicorp_path)

        # Run post-init hooks
        self._run_post_init_hooks(preset, target_path, aicorp_path)

        return aicorp_path

    def _copy_org(self, preset: PresetConfig, aicorp_path: Path):
        """Copy organizational structure from preset"""
        org_path = preset.path / 'org'
        if org_path.exists():
            shutil.copytree(org_path, aicorp_path / 'org')

    def _copy_workflows(self, preset: PresetConfig, aicorp_path: Path):
        """Copy workflow definitions from preset"""
        workflows_path = preset.path / 'workflows'
        if workflows_path.exists():
            shutil.copytree(workflows_path, aicorp_path / 'workflows')

    def _copy_skills(self, preset: PresetConfig, aicorp_path: Path):
        """Copy skills from preset"""
        skills_path = preset.path / 'skills'
        if skills_path.exists():
            shutil.copytree(skills_path, aicorp_path / 'skills')

    def _copy_gates(self, preset: PresetConfig, aicorp_path: Path):
        """Copy gate definitions from preset"""
        gates_path = preset.path / 'gates'
        if gates_path.exists():
            shutil.copytree(gates_path, aicorp_path / 'gate_templates')

    def _copy_config(
        self,
        preset: PresetConfig,
        aicorp_path: Path,
        name: Optional[str],
        customizations: Optional[Dict[str, Any]]
    ):
        """Copy and customize configuration files"""
        config_path = preset.path / 'config'
        target_config = aicorp_path / 'config'

        if config_path.exists():
            shutil.copytree(config_path, target_config)

            # Apply name customization to branding
            if name:
                branding_file = target_config / 'branding.yaml'
                if branding_file.exists():
                    branding = yaml.safe_load(branding_file.read_text())
                    if 'identity' in branding:
                        branding['identity']['name'] = name
                        branding['identity']['legal_name'] = name
                    branding_file.write_text(yaml.dump(branding, default_flow_style=False))

            # Apply other customizations
            if customizations:
                self._apply_customizations(target_config, customizations)

    def _apply_customizations(self, config_path: Path, customizations: Dict[str, Any]):
        """Apply customization overrides to config files"""
        for key, value in customizations.items():
            parts = key.split('.')
            if len(parts) >= 2:
                # Format: file.key.subkey
                file_name = parts[0]
                config_file = config_path / f'{file_name}.yaml'

                if config_file.exists():
                    config = yaml.safe_load(config_file.read_text())

                    # Navigate to the right key
                    current = config
                    for part in parts[1:-1]:
                        if part not in current:
                            current[part] = {}
                        current = current[part]

                    current[parts[-1]] = value
                    config_file.write_text(yaml.dump(config, default_flow_style=False))

    def _create_runtime_dirs(self, aicorp_path: Path):
        """Create empty runtime directories"""
        runtime_dirs = [
            'beads',
            'hooks',
            'molecules/active',
            'molecules/completed',
            'molecules/templates',
            'channels/downchain',
            'channels/upchain',
            'channels/peer',
            'channels/broadcast',
            'pools',
            'memory/organizational',
            'contracts',
            'knowledge'
        ]

        for dir_path in runtime_dirs:
            (aicorp_path / dir_path).mkdir(parents=True, exist_ok=True)

    def _run_post_init_hooks(
        self,
        preset: PresetConfig,
        project_path: Path,
        aicorp_path: Path
    ):
        """Run post-initialization hooks"""
        post_init = preset.hooks.get('post_init', [])

        for hook in post_init:
            action = hook.get('action')

            if action == 'create_directories':
                for path in hook.get('paths', []):
                    (project_path / path).mkdir(parents=True, exist_ok=True)

            elif action == 'create_file':
                file_path = project_path / hook.get('path', '')
                if not file_path.exists():
                    # For now, create empty file
                    # TODO: Support Jinja2 templates
                    file_path.touch()

            elif action == 'git_init':
                if hook.get('if_not_exists', True):
                    git_dir = project_path / '.git'
                    if not git_dir.exists():
                        import subprocess
                        subprocess.run(['git', 'init'], cwd=project_path, capture_output=True)


def list_presets(templates_path: Optional[Path] = None) -> List[PresetMetadata]:
    """Convenience function to list available presets"""
    manager = PresetManager(templates_path)
    return manager.list_presets()


def init_from_preset(
    preset_id: str,
    target_path: Path,
    name: Optional[str] = None,
    customizations: Optional[Dict[str, Any]] = None,
    templates_path: Optional[Path] = None
) -> Path:
    """
    Convenience function to initialize from a preset.

    Args:
        preset_id: The preset to use
        target_path: Where to create the project
        name: Custom name for this corp
        customizations: Optional customization overrides
        templates_path: Optional path to templates directory

    Returns:
        Path to the created .aicorp directory
    """
    manager = PresetManager(templates_path)
    return manager.apply_preset(preset_id, target_path, name, customizations)
