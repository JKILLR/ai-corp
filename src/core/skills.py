"""
Skill System for AI Corp

Provides role-based skill discovery and loading for agents.
Skills are Claude Code skills (SKILL.md files) that give agents
specialized capabilities.

Skill Discovery Layers:
1. User skills (~/.config/claude/skills/)
2. Corp-wide skills (corp/skills/)
3. Department skills (corp/org/departments/{dept}/skills/)
4. Role skills (corp/roles/{role}/skills/)
5. Project skills (.aicorp/skills/)

Higher layers override lower layers for skills with the same name.
"""

import re
import logging
from pathlib import Path
from typing import Optional, List, Dict, Set, Any, Tuple
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# Capability to skill mappings
# NOTE: Each skill should only appear in ONE capability for clean reverse mapping
CAPABILITY_SKILL_MAP: Dict[str, List[str]] = {
    'frontend_design': ['frontend-design', 'artifacts-builder', 'web-artifacts-builder'],
    'testing': ['webapp-testing', 'test-fixing', 'api-tester'],
    'security': ['security-bluebook-builder', 'defense-in-depth', 'varlock-claude-skill'],
    'devops': ['aws-skills', 'terraform-skills', 'ci-cd-automation'],
    'documentation': ['docx', 'pdf', 'internal-comms', 'pptx'],
    'data_analysis': ['xlsx', 'data-analysis', 'log-analysis'],
    'visual_design': ['canvas-design', 'algorithmic-art'],  # Separate from frontend
}

# Reverse mapping: skill -> capability
SKILL_CAPABILITY_MAP: Dict[str, str] = {}
for cap, skills in CAPABILITY_SKILL_MAP.items():
    for skill in skills:
        SKILL_CAPABILITY_MAP[skill] = cap


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Parse YAML frontmatter from SKILL.md content.

    Returns (frontmatter_dict, body_content).
    """
    # Match YAML frontmatter between --- delimiters
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        # No frontmatter, return empty dict and full content
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)

    # Simple YAML parsing (key: value pairs)
    frontmatter = {}
    for line in frontmatter_text.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Handle list values (comma-separated)
            if ',' in value:
                value = [v.strip() for v in value.split(',')]

            frontmatter[key] = value

    return frontmatter, body


@dataclass
class Skill:
    """
    A loaded skill with metadata and content.

    Skills are defined by SKILL.md files with YAML frontmatter
    containing name, description, and optional allowed-tools.
    """
    name: str
    description: str
    path: Path
    allowed_tools: List[str] = field(default_factory=list)
    _content: Optional[str] = field(default=None, repr=False)

    @classmethod
    def from_path(cls, skill_path: Path) -> 'Skill':
        """
        Parse a skill from a directory containing SKILL.md.

        Args:
            skill_path: Path to skill directory

        Returns:
            Skill instance

        Raises:
            ValueError: If SKILL.md doesn't exist or is invalid
        """
        skill_md = skill_path / "SKILL.md"
        if not skill_md.exists():
            raise ValueError(f"No SKILL.md in {skill_path}")

        content = skill_md.read_text()
        frontmatter, body = parse_frontmatter(content)

        # Get name (required)
        name = frontmatter.get('name', skill_path.name)

        # Get description (required)
        description = frontmatter.get('description', '')

        # Get allowed-tools (optional)
        allowed_tools = frontmatter.get('allowed-tools', [])
        if isinstance(allowed_tools, str):
            allowed_tools = [t.strip() for t in allowed_tools.split(',')]

        return cls(
            name=name,
            description=description,
            path=skill_path,
            allowed_tools=allowed_tools,
            _content=None  # Lazy load
        )

    @property
    def content(self) -> str:
        """Lazy load the full skill content"""
        if self._content is None:
            skill_md = self.path / "SKILL.md"
            if skill_md.exists():
                self._content = skill_md.read_text()
            else:
                self._content = ""
        return self._content

    def load_content(self) -> str:
        """Explicitly load and return content"""
        return self.content

    def has_resource(self, name: str) -> bool:
        """Check if skill has a specific resource file"""
        return (self.path / name).exists()

    def get_resource_path(self, name: str) -> Optional[Path]:
        """Get path to a skill resource if it exists"""
        path = self.path / name
        return path if path.exists() else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'path': str(self.path),
            'allowed_tools': self.allowed_tools
        }


class SkillLoader:
    """
    Discovers and loads skills from multiple layers.

    Implements progressive disclosure:
    1. Discovery: Scan directories, load only metadata (~100 tokens per skill)
    2. Loading: Full content loaded only when skill is invoked

    Layers are scanned in order, with later layers overriding earlier
    for skills with the same name.
    """

    def __init__(
        self,
        corp_path: Path,
        project_path: Optional[Path] = None
    ):
        """
        Initialize skill loader.

        Args:
            corp_path: Path to corp directory
            project_path: Optional path to project directory
        """
        self.corp_path = Path(corp_path)
        self.project_path = Path(project_path) if project_path else None
        self._skill_cache: Dict[str, Skill] = {}

    def discover_all_skills(self) -> List[Skill]:
        """
        Discover all skills from all layers.

        Returns skills merged by priority (higher layers override).
        """
        skills = {}

        # Layer 1: User skills (base layer)
        user_skills_path = Path.home() / ".config/claude/skills"
        if user_skills_path.exists():
            for skill in self._scan_directory(user_skills_path):
                skills[skill.name] = skill

        # Layer 2: Corp-wide skills
        corp_skills = self.corp_path / "skills"
        if corp_skills.exists():
            for skill in self._scan_directory(corp_skills):
                skills[skill.name] = skill

        return list(skills.values())

    def discover_skills_for_role(
        self,
        role_id: str,
        department: str
    ) -> List[Skill]:
        """
        Discover all skills available to a specific role.

        Returns skills from all applicable layers, merged by priority:
        User < Corp < Department < Role < Project

        Args:
            role_id: The role identifier (e.g., 'frontend-worker-01')
            department: The department name (e.g., 'engineering')

        Returns:
            List of skills available to this role
        """
        skills = {}

        # Layer 1: User skills (lowest priority in corp context)
        user_skills_path = Path.home() / ".config/claude/skills"
        if user_skills_path.exists():
            for skill in self._scan_directory(user_skills_path):
                skills[skill.name] = skill

        # Layer 2: Corp-wide skills
        corp_skills = self.corp_path / "skills"
        if corp_skills.exists():
            for skill in self._scan_directory(corp_skills):
                skills[skill.name] = skill

        # Layer 3: Department skills
        dept_skills = self.corp_path / "org" / "departments" / department / "skills"
        if dept_skills.exists():
            for skill in self._scan_directory(dept_skills):
                skills[skill.name] = skill

        # Layer 4: Role-specific skills
        role_skills = self.corp_path / "roles" / role_id / "skills"
        if role_skills.exists():
            for skill in self._scan_directory(role_skills):
                skills[skill.name] = skill

        # Layer 5: Project skills (highest priority)
        if self.project_path:
            project_skills = self.project_path / ".aicorp" / "skills"
            if project_skills.exists():
                for skill in self._scan_directory(project_skills):
                    skills[skill.name] = skill

        return list(skills.values())

    def _scan_directory(self, path: Path) -> List[Skill]:
        """
        Scan a directory for skill subdirectories.

        A valid skill directory contains a SKILL.md file.

        Args:
            path: Directory to scan

        Returns:
            List of discovered skills
        """
        skills = []

        if not path.exists() or not path.is_dir():
            return skills

        for item in path.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                try:
                    skill = Skill.from_path(item)
                    skills.append(skill)
                    self._skill_cache[skill.name] = skill
                    logger.debug(f"Loaded skill: {skill.name} from {item}")
                except Exception as e:
                    logger.warning(f"Failed to load skill {item}: {e}")

        return skills

    def get_skill(self, name: str) -> Optional[Skill]:
        """
        Get a skill by name from cache.

        Args:
            name: Skill name

        Returns:
            Skill if found, None otherwise
        """
        return self._skill_cache.get(name)

    def get_skill_names_for_capability(
        self,
        capability: str
    ) -> List[str]:
        """
        Map a capability to skill names.

        Used for capability matching - if work requires 'frontend_design',
        return skills that provide that capability.

        Args:
            capability: Capability name (e.g., 'frontend_design')

        Returns:
            List of skill names that provide this capability
        """
        return CAPABILITY_SKILL_MAP.get(capability, [])

    def clear_cache(self) -> None:
        """Clear the skill cache"""
        self._skill_cache.clear()


class SkillRegistry:
    """
    Central registry mapping roles to their available skills.

    Used by:
    - ClaudeCodeBackend to determine which skills to pass
    - CapabilityMatcher to determine if agent can handle work
    - Dashboard to show agent capabilities
    """

    def __init__(
        self,
        corp_path: Path,
        project_path: Optional[Path] = None
    ):
        """
        Initialize skill registry.

        Args:
            corp_path: Path to corp directory
            project_path: Optional path to project directory
        """
        self.corp_path = Path(corp_path)
        self.project_path = project_path
        self.loader = SkillLoader(corp_path, project_path)

        # Cache: role_id -> List[Skill]
        self._role_skills: Dict[str, List[Skill]] = {}

        # Cache: skill_name -> List[role_id] (reverse lookup)
        self._skill_roles: Dict[str, List[str]] = {}

        # Cache: role_id -> department
        self._role_departments: Dict[str, str] = {}

    def register_role(
        self,
        role_id: str,
        department: str
    ) -> List[Skill]:
        """
        Register a role and discover its skills.

        Args:
            role_id: Role identifier
            department: Department name

        Returns:
            List of skills discovered for this role
        """
        self._role_departments[role_id] = department
        skills = self.loader.discover_skills_for_role(role_id, department)
        self._role_skills[role_id] = skills

        # Build reverse index
        for skill in skills:
            if skill.name not in self._skill_roles:
                self._skill_roles[skill.name] = []
            if role_id not in self._skill_roles[skill.name]:
                self._skill_roles[skill.name].append(role_id)

        logger.info(
            f"Registered role {role_id} with {len(skills)} skills: "
            f"{[s.name for s in skills]}"
        )

        return skills

    def get_skills_for_role(self, role_id: str) -> List[Skill]:
        """
        Get all skills available to a role.

        Args:
            role_id: Role identifier

        Returns:
            List of skills (empty if role not registered)
        """
        return self._role_skills.get(role_id, [])

    def get_skill_names_for_role(self, role_id: str) -> List[str]:
        """
        Get skill names for passing to ClaudeCodeBackend.

        Args:
            role_id: Role identifier

        Returns:
            List of skill names
        """
        return [s.name for s in self.get_skills_for_role(role_id)]

    def get_roles_with_skill(self, skill_name: str) -> List[str]:
        """
        Get all roles that have a specific skill.

        Args:
            skill_name: Name of the skill

        Returns:
            List of role IDs
        """
        return self._skill_roles.get(skill_name, [])

    def can_role_use_skill(self, role_id: str, skill_name: str) -> bool:
        """
        Check if a role has access to a skill.

        Args:
            role_id: Role identifier
            skill_name: Skill name

        Returns:
            True if role has the skill
        """
        return skill_name in self.get_skill_names_for_role(role_id)

    def get_capabilities_for_role(self, role_id: str) -> List[str]:
        """
        Convert role's skills to capabilities.

        This bridges the skill system with the existing
        capability-based work matching in HookManager.

        Args:
            role_id: Role identifier

        Returns:
            List of capability names derived from skills
        """
        skills = self.get_skills_for_role(role_id)
        capabilities: Set[str] = set()

        for skill in skills:
            if skill.name in SKILL_CAPABILITY_MAP:
                capabilities.add(SKILL_CAPABILITY_MAP[skill.name])

        return list(capabilities)

    def find_roles_with_capability(self, capability: str) -> List[str]:
        """
        Find all roles that have a specific capability.

        Args:
            capability: Capability name (e.g., 'frontend_design')

        Returns:
            List of role IDs with this capability
        """
        skill_names = CAPABILITY_SKILL_MAP.get(capability, [])
        roles: Set[str] = set()

        for skill_name in skill_names:
            roles.update(self.get_roles_with_skill(skill_name))

        return list(roles)

    def get_skill_summary(self) -> Dict[str, Any]:
        """
        Get a summary of all registered skills.

        Returns:
            Dictionary with skill statistics
        """
        all_skills: Set[str] = set()
        for skills in self._role_skills.values():
            all_skills.update(s.name for s in skills)

        return {
            'total_roles': len(self._role_skills),
            'total_unique_skills': len(all_skills),
            'skill_names': sorted(all_skills),
            'roles_by_skill_count': {
                role_id: len(skills)
                for role_id, skills in self._role_skills.items()
            }
        }

    def refresh_role(self, role_id: str) -> List[Skill]:
        """
        Refresh skills for a role (re-scan directories).

        Args:
            role_id: Role identifier

        Returns:
            Updated list of skills
        """
        department = self._role_departments.get(role_id, 'engineering')

        # Clear old entries from reverse index
        old_skills = self._role_skills.get(role_id, [])
        for skill in old_skills:
            if skill.name in self._skill_roles:
                self._skill_roles[skill.name] = [
                    r for r in self._skill_roles[skill.name]
                    if r != role_id
                ]

        # Re-register
        return self.register_role(role_id, department)

    def clear(self) -> None:
        """Clear all registrations"""
        self._role_skills.clear()
        self._skill_roles.clear()
        self._role_departments.clear()
        self.loader.clear_cache()
