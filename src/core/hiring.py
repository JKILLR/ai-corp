"""
Hiring System - Dynamic Agent Onboarding

The hiring system allows new departments, roles, and workers to be
added at runtime without code changes. Simply define a role in YAML
and "hire" the agent.

Key features:
- Dynamic role creation from templates
- Automatic hook and pool setup
- Hot-reload of organizational structure
- Industry-agnostic templates
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml


class HiringManager:
    """
    Manages dynamic onboarding of new agents.

    Allows the organization to grow by:
    - Adding new departments
    - Creating new roles
    - Hiring workers into pools
    - All without code changes
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.org_path = self.corp_path / "org"
        self.departments_path = self.org_path / "departments"
        self.roles_path = self.org_path / "roles"

        # Ensure paths exist
        self.departments_path.mkdir(parents=True, exist_ok=True)
        self.roles_path.mkdir(parents=True, exist_ok=True)

    def create_department(
        self,
        department_id: str,
        name: str,
        head_role: str,
        mission: str,
        directors: List[Dict[str, Any]],
        worker_pools: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a new department dynamically.

        Args:
            department_id: Unique ID (e.g., 'manufacturing')
            name: Display name (e.g., 'Manufacturing Department')
            head_role: VP role ID (e.g., 'vp_manufacturing')
            mission: Department mission statement
            directors: List of director definitions
            worker_pools: List of worker pool definitions

        Returns:
            Created department configuration
        """
        department = {
            'department': {
                'id': department_id,
                'name': name,
                'head': head_role,
                'description': mission
            },
            'mission': mission,
            'directors': directors,
            'worker_pools': worker_pools or []
        }

        # Save to file
        dept_file = self.departments_path / f"{department_id}.yaml"
        dept_file.write_text(yaml.dump(department, default_flow_style=False, sort_keys=False))

        print(f"[Hiring] Created department: {name}")
        return department

    def hire_vp(
        self,
        role_id: str,
        name: str,
        department: str,
        responsibilities: List[str],
        skills: Optional[List[str]] = None,
        direct_reports: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Hire a new VP to lead a department.

        All VPs are Claude Opus 4.5 with full capabilities.
        """
        vp_role = {
            'id': role_id,
            'name': name,
            'type': 'vice_president',
            'level': 2,
            'department': department,
            'description': f"Leads the {department} department",
            'is_human': False,
            'model': 'claude-opus-4-5-20251101',
            'skills': skills or [],
            'responsibilities': responsibilities,
            'communication': {
                'receives_from': ['coo'] + (direct_reports or []),
                'sends_to': ['coo'] + (direct_reports or []),
            },
            'authority': [
                'assign_to_directors',
                'approve_decisions',
                'manage_worker_pools',
                'escalate_to_coo'
            ]
        }

        self._add_role_to_file('vp', vp_role)
        self._update_hierarchy_for_vp(role_id)

        print(f"[Hiring] Hired VP: {name}")
        return vp_role

    def hire_director(
        self,
        role_id: str,
        name: str,
        department: str,
        reports_to: str,
        focus: str,
        responsibilities: List[str],
        skills: Optional[List[str]] = None,
        manages_pool: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Hire a new Director.

        All Directors are Claude Opus 4.5 with full capabilities.
        """
        director_role = {
            'id': role_id,
            'name': name,
            'type': 'director',
            'level': 3,
            'department': department,
            'reports_to': reports_to,
            'description': focus,
            'is_human': False,
            'model': 'claude-opus-4-5-20251101',
            'skills': skills or [],
            'manages_pool': manages_pool,
            'responsibilities': responsibilities
        }

        self._add_role_to_file('director', director_role)

        print(f"[Hiring] Hired Director: {name}")
        return director_role

    def hire_worker(
        self,
        role_id: str,
        name: str,
        department: str,
        pool: str,
        director: str,
        description: str,
        capabilities: List[str],
        responsibilities: List[str],
        skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Hire a new Worker into a pool.

        All Workers are Claude Opus 4.5 with full capabilities.
        The 'capabilities' field is for task routing, not restrictions.
        """
        worker_role = {
            'id': role_id,
            'name': name,
            'type': 'worker',
            'level': 4,
            'department': department,
            'pool': pool,
            'director': director,
            'description': description,
            'is_human': False,
            'model': 'claude-opus-4-5-20251101',
            'skills': skills or [],
            'capabilities': capabilities,
            'responsibilities': responsibilities
        }

        self._add_role_to_file('worker', worker_role)

        print(f"[Hiring] Hired Worker: {name}")
        return worker_role

    def create_worker_pool(
        self,
        pool_id: str,
        name: str,
        department: str,
        director: str,
        min_workers: int = 1,
        max_workers: int = 5,
        capabilities: Optional[List[str]] = None,
        skills: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new worker pool for a department.
        """
        from ..core.pool import PoolManager

        pool_manager = PoolManager(self.corp_path)
        pool = pool_manager.create_pool(
            name=name,
            department=department,
            director_id=director,
            min_workers=min_workers,
            max_workers=max_workers,
            required_capabilities=capabilities or [],
            required_skills=skills or []
        )

        print(f"[Hiring] Created pool: {name}")
        return pool.to_dict()

    def _add_role_to_file(self, role_type: str, role: Dict[str, Any]) -> None:
        """Add a role to the appropriate roles file"""
        roles_file = self.roles_path / f"{role_type}.yaml"

        if roles_file.exists():
            data = yaml.safe_load(roles_file.read_text())
        else:
            data = {'roles': []}

        # Check if role already exists
        existing_ids = {r['id'] for r in data.get('roles', [])}
        if role['id'] in existing_ids:
            # Update existing
            data['roles'] = [
                role if r['id'] == role['id'] else r
                for r in data['roles']
            ]
        else:
            # Add new
            data['roles'].append(role)

        roles_file.write_text(yaml.dump(data, default_flow_style=False, sort_keys=False))

    def _update_hierarchy_for_vp(self, vp_role_id: str) -> None:
        """Update hierarchy to include new VP"""
        hierarchy_file = self.org_path / "hierarchy.yaml"

        if hierarchy_file.exists():
            hierarchy = yaml.safe_load(hierarchy_file.read_text())
        else:
            hierarchy = {'reporting_chains': {'coo': {'direct_reports': []}}}

        # Add VP to COO's direct reports
        coo_reports = hierarchy.get('reporting_chains', {}).get('coo', {}).get('direct_reports', [])
        if vp_role_id not in coo_reports:
            coo_reports.append(vp_role_id)
            hierarchy['reporting_chains']['coo']['direct_reports'] = coo_reports

        # Add VP's reporting chain
        hierarchy['reporting_chains'][vp_role_id] = {
            'reports_to': 'coo',
            'direct_reports': []
        }

        hierarchy_file.write_text(yaml.dump(hierarchy, default_flow_style=False, sort_keys=False))

    def list_all_roles(self) -> Dict[str, List[Dict[str, Any]]]:
        """List all roles in the organization"""
        all_roles = {
            'executives': [],
            'vps': [],
            'directors': [],
            'workers': []
        }

        for role_file in self.roles_path.glob("*.yaml"):
            data = yaml.safe_load(role_file.read_text())
            for role in data.get('roles', []):
                role_type = role.get('type', 'worker')
                if role_type == 'executive':
                    all_roles['executives'].append(role)
                elif role_type == 'vice_president':
                    all_roles['vps'].append(role)
                elif role_type == 'director':
                    all_roles['directors'].append(role)
                else:
                    all_roles['workers'].append(role)

        return all_roles

    def get_org_chart(self) -> str:
        """Generate a text org chart"""
        roles = self.list_all_roles()

        chart = """
AI Corp Organization
====================

CEO (Human)
  │
  └── COO (AI Orchestrator)
"""

        for vp in roles['vps']:
            chart += f"        │\n        ├── {vp['name']} ({vp['id']})\n"

            # Find directors for this VP
            vp_directors = [
                d for d in roles['directors']
                if d.get('reports_to') == vp['id']
            ]

            for i, director in enumerate(vp_directors):
                prefix = "│       └──" if i == len(vp_directors) - 1 else "│       ├──"
                chart += f"        {prefix} {director['name']}\n"

                # Find workers for this director
                dir_workers = [
                    w for w in roles['workers']
                    if w.get('director') == director['id']
                ]

                if dir_workers:
                    pool_name = dir_workers[0].get('pool', 'workers')
                    chart += f"        │           └── [{pool_name}: {len(dir_workers)} workers]\n"

        return chart


def quick_hire(corp_path: Path, role_type: str, **kwargs) -> Dict[str, Any]:
    """
    Quick hire function for adding agents.

    Examples:
        quick_hire(corp_path, 'vp',
            role_id='vp_manufacturing',
            name='VP of Manufacturing',
            department='manufacturing',
            responsibilities=['Oversee production', 'Manage quality']
        )

        quick_hire(corp_path, 'worker',
            role_id='assembly_worker',
            name='Assembly Technician',
            department='manufacturing',
            pool='pool_assembly',
            director='dir_assembly',
            description='Assembles components',
            capabilities=['assembly', 'quality_check'],
            responsibilities=['Assemble products', 'Report defects']
        )
    """
    manager = HiringManager(corp_path)

    if role_type == 'vp':
        return manager.hire_vp(**kwargs)
    elif role_type == 'director':
        return manager.hire_director(**kwargs)
    elif role_type == 'worker':
        return manager.hire_worker(**kwargs)
    elif role_type == 'department':
        return manager.create_department(**kwargs)
    else:
        raise ValueError(f"Unknown role type: {role_type}")
