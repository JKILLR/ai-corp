"""
Tests for the Skill System.

Tests skill discovery, loading, and registry functionality.
"""

import pytest
from pathlib import Path

from src.core.skills import (
    Skill, SkillLoader, SkillRegistry,
    parse_frontmatter, CAPABILITY_SKILL_MAP, SKILL_CAPABILITY_MAP
)


class TestParseFrontmatter:
    """Tests for frontmatter parsing"""

    def test_parse_simple_frontmatter(self):
        """Test parsing simple YAML frontmatter"""
        content = """---
name: test-skill
description: A test skill
---

# Test Skill

This is the body.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter['name'] == 'test-skill'
        assert frontmatter['description'] == 'A test skill'
        assert '# Test Skill' in body

    def test_parse_frontmatter_with_allowed_tools(self):
        """Test parsing frontmatter with allowed-tools list"""
        content = """---
name: read-only
description: Read-only skill
allowed-tools: Read, Grep, Glob
---

Body content.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter['name'] == 'read-only'
        assert frontmatter['allowed-tools'] == ['Read', 'Grep', 'Glob']

    def test_parse_no_frontmatter(self):
        """Test parsing content without frontmatter"""
        content = "Just regular content\nNo frontmatter here."
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert body == content

    def test_parse_empty_frontmatter(self):
        """Test parsing empty frontmatter"""
        content = """---
---

Body only.
"""
        frontmatter, body = parse_frontmatter(content)

        assert frontmatter == {}
        assert 'Body only' in body


class TestSkill:
    """Tests for Skill class"""

    @pytest.fixture
    def skill_dir(self, tmp_path):
        """Create a skill directory with SKILL.md"""
        skill_path = tmp_path / "test-skill"
        skill_path.mkdir()

        skill_md = skill_path / "SKILL.md"
        skill_md.write_text("""---
name: test-skill
description: A test skill for unit testing
allowed-tools: Read, Write
---

# Test Skill

## Instructions

Use this skill when testing.
""")
        return skill_path

    def test_from_path(self, skill_dir):
        """Test loading skill from path"""
        skill = Skill.from_path(skill_dir)

        assert skill.name == "test-skill"
        assert skill.description == "A test skill for unit testing"
        assert skill.allowed_tools == ['Read', 'Write']
        assert skill.path == skill_dir

    def test_from_path_missing_skill_md(self, tmp_path):
        """Test error when SKILL.md is missing"""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()

        with pytest.raises(ValueError, match="No SKILL.md"):
            Skill.from_path(empty_dir)

    def test_lazy_content_loading(self, skill_dir):
        """Test that content is lazy loaded"""
        skill = Skill.from_path(skill_dir)

        # Content should not be loaded yet
        assert skill._content is None

        # Access content
        content = skill.content

        assert skill._content is not None
        assert "# Test Skill" in content

    def test_load_content_method(self, skill_dir):
        """Test explicit content loading"""
        skill = Skill.from_path(skill_dir)
        content = skill.load_content()

        assert "## Instructions" in content

    def test_to_dict(self, skill_dir):
        """Test conversion to dictionary"""
        skill = Skill.from_path(skill_dir)
        data = skill.to_dict()

        assert data['name'] == 'test-skill'
        assert data['description'] == 'A test skill for unit testing'
        assert data['allowed_tools'] == ['Read', 'Write']
        assert str(skill_dir) in data['path']

    def test_has_resource(self, skill_dir):
        """Test checking for resources"""
        skill = Skill.from_path(skill_dir)

        # SKILL.md should exist
        assert skill.has_resource("SKILL.md")

        # Random file should not exist
        assert not skill.has_resource("nonexistent.txt")

    def test_get_resource_path(self, skill_dir):
        """Test getting resource paths"""
        skill = Skill.from_path(skill_dir)

        # Existing resource
        path = skill.get_resource_path("SKILL.md")
        assert path is not None
        assert path.exists()

        # Non-existing resource
        path = skill.get_resource_path("nonexistent.txt")
        assert path is None

    def test_default_name_from_directory(self, tmp_path):
        """Test that name defaults to directory name"""
        skill_path = tmp_path / "my-awesome-skill"
        skill_path.mkdir()

        skill_md = skill_path / "SKILL.md"
        skill_md.write_text("""---
description: No name specified
---

Body.
""")
        skill = Skill.from_path(skill_path)

        assert skill.name == "my-awesome-skill"


class TestSkillLoader:
    """Tests for SkillLoader class"""

    @pytest.fixture
    def skill_dirs(self, tmp_path):
        """Create a skill directory structure"""
        # Corp-wide skills
        corp_skills = tmp_path / "skills"
        corp_skills.mkdir()

        (corp_skills / "code-review").mkdir()
        (corp_skills / "code-review" / "SKILL.md").write_text("""---
name: code-review
description: Code review skill
---

Review code.
""")

        # Department skills
        dept_skills = tmp_path / "org" / "departments" / "engineering" / "skills"
        dept_skills.mkdir(parents=True)

        (dept_skills / "architecture").mkdir()
        (dept_skills / "architecture" / "SKILL.md").write_text("""---
name: architecture
description: Architecture patterns
---

Architecture skill.
""")

        # Role skills
        role_skills = tmp_path / "roles" / "frontend-worker" / "skills"
        role_skills.mkdir(parents=True)

        (role_skills / "frontend-design").mkdir()
        (role_skills / "frontend-design" / "SKILL.md").write_text("""---
name: frontend-design
description: Frontend design skill
---

Design frontends.
""")

        return tmp_path

    def test_discover_all_skills(self, skill_dirs):
        """Test discovering all corp-wide skills"""
        loader = SkillLoader(skill_dirs)
        skills = loader.discover_all_skills()

        skill_names = [s.name for s in skills]
        assert "code-review" in skill_names

    def test_discover_skills_for_role(self, skill_dirs):
        """Test discovering skills for a specific role"""
        loader = SkillLoader(skill_dirs)
        skills = loader.discover_skills_for_role(
            role_id="frontend-worker",
            department="engineering"
        )

        skill_names = [s.name for s in skills]

        # Should have corp, department, and role skills
        assert "code-review" in skill_names
        assert "architecture" in skill_names
        assert "frontend-design" in skill_names

    def test_skill_caching(self, skill_dirs):
        """Test that skills are cached"""
        loader = SkillLoader(skill_dirs)

        # First load
        loader.discover_all_skills()

        # Should be in cache
        skill = loader.get_skill("code-review")
        assert skill is not None
        assert skill.name == "code-review"

    def test_get_skill_not_found(self, skill_dirs):
        """Test getting a skill that doesn't exist"""
        loader = SkillLoader(skill_dirs)

        skill = loader.get_skill("nonexistent")
        assert skill is None

    def test_clear_cache(self, skill_dirs):
        """Test clearing the skill cache"""
        loader = SkillLoader(skill_dirs)
        loader.discover_all_skills()

        # Should be in cache
        assert loader.get_skill("code-review") is not None

        loader.clear_cache()

        # Should be gone
        assert loader.get_skill("code-review") is None

    def test_get_skill_names_for_capability(self, skill_dirs):
        """Test mapping capability to skill names"""
        loader = SkillLoader(skill_dirs)

        skills = loader.get_skill_names_for_capability("frontend_design")
        assert "frontend-design" in skills

    def test_empty_directory(self, tmp_path):
        """Test loading from empty directory"""
        loader = SkillLoader(tmp_path)
        skills = loader.discover_all_skills()

        assert skills == []


class TestSkillRegistry:
    """Tests for SkillRegistry class"""

    @pytest.fixture
    def registry_setup(self, tmp_path):
        """Set up a skill registry with some skills"""
        # Create skills
        corp_skills = tmp_path / "skills"
        corp_skills.mkdir()

        (corp_skills / "internal-comms").mkdir()
        (corp_skills / "internal-comms" / "SKILL.md").write_text("""---
name: internal-comms
description: Internal communications
---
""")

        dept_skills = tmp_path / "org" / "departments" / "engineering" / "skills"
        dept_skills.mkdir(parents=True)

        (dept_skills / "code-review").mkdir()
        (dept_skills / "code-review" / "SKILL.md").write_text("""---
name: code-review
description: Code review
---
""")

        role_skills = tmp_path / "roles" / "vp-engineering" / "skills"
        role_skills.mkdir(parents=True)

        (role_skills / "aws-skills").mkdir()
        (role_skills / "aws-skills" / "SKILL.md").write_text("""---
name: aws-skills
description: AWS skills
---
""")

        return tmp_path

    def test_register_role(self, registry_setup):
        """Test registering a role"""
        registry = SkillRegistry(registry_setup)
        skills = registry.register_role("vp-engineering", "engineering")

        skill_names = [s.name for s in skills]
        assert "internal-comms" in skill_names  # Corp-wide
        assert "code-review" in skill_names  # Department
        assert "aws-skills" in skill_names  # Role

    def test_get_skills_for_role(self, registry_setup):
        """Test getting skills for a registered role"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        skills = registry.get_skills_for_role("vp-engineering")
        assert len(skills) >= 3

    def test_get_skill_names_for_role(self, registry_setup):
        """Test getting skill names for a role"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        names = registry.get_skill_names_for_role("vp-engineering")
        assert "internal-comms" in names
        assert "code-review" in names
        assert "aws-skills" in names

    def test_get_roles_with_skill(self, registry_setup):
        """Test finding roles that have a skill"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")
        registry.register_role("dir-frontend", "engineering")

        roles = registry.get_roles_with_skill("code-review")
        assert "vp-engineering" in roles
        assert "dir-frontend" in roles

    def test_can_role_use_skill(self, registry_setup):
        """Test checking if role can use skill"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        assert registry.can_role_use_skill("vp-engineering", "aws-skills")
        assert not registry.can_role_use_skill("vp-engineering", "nonexistent")

    def test_get_capabilities_for_role(self, registry_setup):
        """Test getting capabilities from skills"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        capabilities = registry.get_capabilities_for_role("vp-engineering")
        # aws-skills maps to 'devops' capability
        assert "devops" in capabilities

    def test_find_roles_with_capability(self, registry_setup):
        """Test finding roles with a capability"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        roles = registry.find_roles_with_capability("devops")
        assert "vp-engineering" in roles

    def test_get_skill_summary(self, registry_setup):
        """Test getting skill summary"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        summary = registry.get_skill_summary()

        assert summary['total_roles'] == 1
        assert summary['total_unique_skills'] >= 3
        assert "internal-comms" in summary['skill_names']

    def test_refresh_role(self, registry_setup):
        """Test refreshing role skills"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        # Add a new skill
        new_skill = registry_setup / "roles" / "vp-engineering" / "skills" / "new-skill"
        new_skill.mkdir()
        (new_skill / "SKILL.md").write_text("""---
name: new-skill
description: New skill
---
""")

        # Refresh
        skills = registry.refresh_role("vp-engineering")
        skill_names = [s.name for s in skills]

        assert "new-skill" in skill_names

    def test_clear_registry(self, registry_setup):
        """Test clearing the registry"""
        registry = SkillRegistry(registry_setup)
        registry.register_role("vp-engineering", "engineering")

        assert len(registry.get_skills_for_role("vp-engineering")) > 0

        registry.clear()

        assert len(registry.get_skills_for_role("vp-engineering")) == 0

    def test_unregistered_role(self, registry_setup):
        """Test getting skills for unregistered role"""
        registry = SkillRegistry(registry_setup)

        skills = registry.get_skills_for_role("nonexistent")
        assert skills == []


class TestCapabilityMappings:
    """Tests for capability-skill mappings"""

    def test_capability_to_skills(self):
        """Test capability to skills mapping exists"""
        assert "frontend_design" in CAPABILITY_SKILL_MAP
        assert "frontend-design" in CAPABILITY_SKILL_MAP["frontend_design"]

    def test_skill_to_capability(self):
        """Test skill to capability reverse mapping"""
        assert "frontend-design" in SKILL_CAPABILITY_MAP
        assert SKILL_CAPABILITY_MAP["frontend-design"] == "frontend_design"

    def test_all_skills_have_reverse_mapping(self):
        """Test that all skills in cap map have reverse mapping"""
        for cap, skills in CAPABILITY_SKILL_MAP.items():
            for skill in skills:
                assert skill in SKILL_CAPABILITY_MAP
                assert SKILL_CAPABILITY_MAP[skill] == cap


class TestSkillWithSubdirectories:
    """Tests for skills with additional subdirectories"""

    @pytest.fixture
    def complex_skill(self, tmp_path):
        """Create a skill with scripts and references"""
        skill_path = tmp_path / "complex-skill"
        skill_path.mkdir()

        # Main skill file
        (skill_path / "SKILL.md").write_text("""---
name: complex-skill
description: A skill with resources
---

# Complex Skill

Use scripts/ for automation.
""")

        # Scripts directory
        scripts = skill_path / "scripts"
        scripts.mkdir()
        (scripts / "setup.sh").write_text("#!/bin/bash\necho 'Setup'")

        # References directory
        refs = skill_path / "references"
        refs.mkdir()
        (refs / "guide.md").write_text("# Guide\nReference documentation.")

        return skill_path

    def test_load_skill_with_resources(self, complex_skill):
        """Test loading skill with subdirectories"""
        skill = Skill.from_path(complex_skill)

        assert skill.name == "complex-skill"
        assert skill.has_resource("scripts/setup.sh")
        assert skill.has_resource("references/guide.md")

    def test_get_script_path(self, complex_skill):
        """Test getting path to script"""
        skill = Skill.from_path(complex_skill)

        path = skill.get_resource_path("scripts/setup.sh")
        assert path is not None
        assert path.read_text().startswith("#!/bin/bash")
