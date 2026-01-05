"""
Industry Templates - Apply AI Corp to Any Domain

Templates allow AI Corp to be configured for different industries:
- Software Development (default)
- Construction & Architecture
- Research & Academia
- Business & Consulting
- Manufacturing
- Healthcare
- Legal
- Creative Agency

Each template defines:
- Departments appropriate for the industry
- Roles with industry-specific focus
- Quality gates relevant to the domain
- Molecule templates for common workflows
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import shutil

from .hiring import HiringManager


# =============================================================================
# INDUSTRY TEMPLATE DEFINITIONS
# =============================================================================

INDUSTRY_TEMPLATES = {
    'software': {
        'name': 'Software Development',
        'description': 'Technology product development organization',
        'departments': [
            {
                'id': 'engineering',
                'name': 'Engineering Department',
                'vp': 'vp_engineering',
                'directors': [
                    {'id': 'dir_architecture', 'name': 'Architecture Director', 'focus': 'System design'},
                    {'id': 'dir_frontend', 'name': 'Frontend Director', 'focus': 'UI/UX implementation', 'skills': ['frontend-design']},
                    {'id': 'dir_backend', 'name': 'Backend Director', 'focus': 'APIs and services'},
                    {'id': 'dir_devops', 'name': 'DevOps Director', 'focus': 'Infrastructure', 'skills': ['aws-skills', 'terraform-skills']},
                ],
                'worker_types': ['frontend_engineer', 'backend_engineer', 'devops_engineer']
            },
            {
                'id': 'product',
                'name': 'Product Department',
                'vp': 'vp_product',
                'directors': [
                    {'id': 'dir_product', 'name': 'Product Director', 'focus': 'Roadmap and requirements'},
                    {'id': 'dir_design', 'name': 'Design Director', 'focus': 'UX and visual design', 'skills': ['frontend-design']},
                ],
                'worker_types': ['product_manager', 'ux_designer']
            },
            {
                'id': 'quality',
                'name': 'Quality Department',
                'vp': 'vp_quality',
                'directors': [
                    {'id': 'dir_qa', 'name': 'QA Director', 'focus': 'Testing', 'skills': ['webapp-testing']},
                    {'id': 'dir_security', 'name': 'Security Director', 'focus': 'Security review', 'skills': ['security-bluebook-builder']},
                ],
                'worker_types': ['qa_engineer', 'security_reviewer', 'code_reviewer']
            },
        ],
        'quality_gates': ['research', 'design', 'build', 'qa', 'security'],
        'molecule_templates': ['feature', 'bugfix', 'research']
    },

    'construction': {
        'name': 'Construction & Architecture',
        'description': 'Building and construction project management',
        'departments': [
            {
                'id': 'design',
                'name': 'Design & Architecture',
                'vp': 'vp_design',
                'directors': [
                    {'id': 'dir_architecture', 'name': 'Chief Architect', 'focus': 'Building design and blueprints'},
                    {'id': 'dir_structural', 'name': 'Structural Director', 'focus': 'Structural engineering'},
                    {'id': 'dir_mep', 'name': 'MEP Director', 'focus': 'Mechanical, electrical, plumbing'},
                ],
                'worker_types': ['architect', 'structural_engineer', 'mep_engineer']
            },
            {
                'id': 'construction',
                'name': 'Construction Management',
                'vp': 'vp_construction',
                'directors': [
                    {'id': 'dir_site', 'name': 'Site Director', 'focus': 'On-site operations'},
                    {'id': 'dir_procurement', 'name': 'Procurement Director', 'focus': 'Materials and vendors'},
                    {'id': 'dir_scheduling', 'name': 'Scheduling Director', 'focus': 'Timeline management'},
                ],
                'worker_types': ['site_manager', 'procurement_specialist', 'scheduler']
            },
            {
                'id': 'compliance',
                'name': 'Compliance & Safety',
                'vp': 'vp_compliance',
                'directors': [
                    {'id': 'dir_safety', 'name': 'Safety Director', 'focus': 'Workplace safety'},
                    {'id': 'dir_permits', 'name': 'Permits Director', 'focus': 'Regulatory compliance'},
                    {'id': 'dir_quality', 'name': 'Quality Director', 'focus': 'Construction quality'},
                ],
                'worker_types': ['safety_inspector', 'permit_coordinator', 'quality_inspector']
            },
        ],
        'quality_gates': ['design_review', 'permit_approval', 'inspection', 'safety_check', 'final_inspection'],
        'molecule_templates': ['new_building', 'renovation', 'inspection']
    },

    'research': {
        'name': 'Research & Academia',
        'description': 'Scientific research organization',
        'departments': [
            {
                'id': 'research',
                'name': 'Research Division',
                'vp': 'vp_research',
                'directors': [
                    {'id': 'dir_principal', 'name': 'Principal Investigator', 'focus': 'Research direction'},
                    {'id': 'dir_methodology', 'name': 'Methodology Director', 'focus': 'Research methods'},
                    {'id': 'dir_data', 'name': 'Data Science Director', 'focus': 'Data analysis'},
                ],
                'worker_types': ['researcher', 'data_scientist', 'lab_technician']
            },
            {
                'id': 'publications',
                'name': 'Publications & Grants',
                'vp': 'vp_publications',
                'directors': [
                    {'id': 'dir_writing', 'name': 'Scientific Writing Director', 'focus': 'Paper writing'},
                    {'id': 'dir_grants', 'name': 'Grants Director', 'focus': 'Funding acquisition'},
                    {'id': 'dir_review', 'name': 'Peer Review Director', 'focus': 'Quality review'},
                ],
                'worker_types': ['scientific_writer', 'grant_writer', 'peer_reviewer']
            },
            {
                'id': 'ethics',
                'name': 'Ethics & Compliance',
                'vp': 'vp_ethics',
                'directors': [
                    {'id': 'dir_irb', 'name': 'IRB Director', 'focus': 'Human subjects protection'},
                    {'id': 'dir_integrity', 'name': 'Research Integrity Director', 'focus': 'Scientific integrity'},
                ],
                'worker_types': ['ethics_reviewer', 'compliance_officer']
            },
        ],
        'quality_gates': ['proposal_review', 'methodology_approval', 'data_validation', 'peer_review', 'publication_ready'],
        'molecule_templates': ['research_project', 'grant_proposal', 'paper_submission']
    },

    'business': {
        'name': 'Business & Consulting',
        'description': 'Business consulting and strategy organization',
        'departments': [
            {
                'id': 'strategy',
                'name': 'Strategy & Analysis',
                'vp': 'vp_strategy',
                'directors': [
                    {'id': 'dir_strategy', 'name': 'Strategy Director', 'focus': 'Business strategy'},
                    {'id': 'dir_market', 'name': 'Market Analysis Director', 'focus': 'Market research'},
                    {'id': 'dir_competitive', 'name': 'Competitive Intelligence Director', 'focus': 'Competitor analysis'},
                ],
                'worker_types': ['strategist', 'market_analyst', 'competitive_analyst']
            },
            {
                'id': 'operations',
                'name': 'Operations Consulting',
                'vp': 'vp_operations',
                'directors': [
                    {'id': 'dir_process', 'name': 'Process Improvement Director', 'focus': 'Process optimization'},
                    {'id': 'dir_change', 'name': 'Change Management Director', 'focus': 'Organizational change'},
                    {'id': 'dir_implementation', 'name': 'Implementation Director', 'focus': 'Solution deployment'},
                ],
                'worker_types': ['process_consultant', 'change_specialist', 'implementation_consultant']
            },
            {
                'id': 'client',
                'name': 'Client Relations',
                'vp': 'vp_client',
                'directors': [
                    {'id': 'dir_engagement', 'name': 'Engagement Director', 'focus': 'Client engagements'},
                    {'id': 'dir_delivery', 'name': 'Delivery Director', 'focus': 'Project delivery'},
                ],
                'worker_types': ['engagement_manager', 'delivery_consultant']
            },
        ],
        'quality_gates': ['proposal_review', 'analysis_complete', 'recommendation_review', 'client_approval', 'implementation_review'],
        'molecule_templates': ['consulting_engagement', 'market_analysis', 'strategy_development']
    },

    'manufacturing': {
        'name': 'Manufacturing',
        'description': 'Product manufacturing organization',
        'departments': [
            {
                'id': 'production',
                'name': 'Production',
                'vp': 'vp_production',
                'directors': [
                    {'id': 'dir_assembly', 'name': 'Assembly Director', 'focus': 'Product assembly'},
                    {'id': 'dir_machining', 'name': 'Machining Director', 'focus': 'Parts fabrication'},
                    {'id': 'dir_packaging', 'name': 'Packaging Director', 'focus': 'Final packaging'},
                ],
                'worker_types': ['assembly_tech', 'machinist', 'packaging_tech']
            },
            {
                'id': 'quality_control',
                'name': 'Quality Control',
                'vp': 'vp_quality',
                'directors': [
                    {'id': 'dir_inspection', 'name': 'Inspection Director', 'focus': 'Product inspection'},
                    {'id': 'dir_testing', 'name': 'Testing Director', 'focus': 'Product testing'},
                    {'id': 'dir_standards', 'name': 'Standards Director', 'focus': 'Quality standards'},
                ],
                'worker_types': ['inspector', 'tester', 'standards_analyst']
            },
            {
                'id': 'supply_chain',
                'name': 'Supply Chain',
                'vp': 'vp_supply_chain',
                'directors': [
                    {'id': 'dir_procurement', 'name': 'Procurement Director', 'focus': 'Materials sourcing'},
                    {'id': 'dir_inventory', 'name': 'Inventory Director', 'focus': 'Inventory management'},
                    {'id': 'dir_logistics', 'name': 'Logistics Director', 'focus': 'Shipping and receiving'},
                ],
                'worker_types': ['procurement_specialist', 'inventory_analyst', 'logistics_coordinator']
            },
        ],
        'quality_gates': ['materials_inspection', 'in_process_check', 'final_inspection', 'packaging_check', 'shipping_approval'],
        'molecule_templates': ['production_run', 'quality_audit', 'supplier_evaluation']
    },

    'creative': {
        'name': 'Creative Agency',
        'description': 'Marketing and creative services organization',
        'departments': [
            {
                'id': 'creative',
                'name': 'Creative',
                'vp': 'vp_creative',
                'directors': [
                    {'id': 'dir_art', 'name': 'Art Director', 'focus': 'Visual design', 'skills': ['frontend-design']},
                    {'id': 'dir_copy', 'name': 'Copy Director', 'focus': 'Copywriting'},
                    {'id': 'dir_video', 'name': 'Video Director', 'focus': 'Video production'},
                ],
                'worker_types': ['graphic_designer', 'copywriter', 'video_editor']
            },
            {
                'id': 'strategy',
                'name': 'Strategy & Planning',
                'vp': 'vp_strategy',
                'directors': [
                    {'id': 'dir_brand', 'name': 'Brand Strategy Director', 'focus': 'Brand development'},
                    {'id': 'dir_media', 'name': 'Media Planning Director', 'focus': 'Media strategy'},
                    {'id': 'dir_analytics', 'name': 'Analytics Director', 'focus': 'Campaign analytics'},
                ],
                'worker_types': ['brand_strategist', 'media_planner', 'analytics_specialist']
            },
            {
                'id': 'account',
                'name': 'Account Management',
                'vp': 'vp_accounts',
                'directors': [
                    {'id': 'dir_account', 'name': 'Account Director', 'focus': 'Client relationships'},
                    {'id': 'dir_project', 'name': 'Project Director', 'focus': 'Project delivery'},
                ],
                'worker_types': ['account_manager', 'project_coordinator']
            },
        ],
        'quality_gates': ['creative_brief', 'concept_review', 'client_review', 'final_approval', 'delivery'],
        'molecule_templates': ['campaign', 'brand_identity', 'content_creation']
    },
}


class IndustryTemplateManager:
    """
    Manages industry templates for AI Corp.

    Allows the system to be configured for any industry by:
    1. Selecting a template
    2. Customizing departments and roles
    3. Generating the full organizational structure
    """

    def __init__(self, corp_path: Path):
        self.corp_path = Path(corp_path)
        self.hiring = HiringManager(corp_path)
        self.templates_path = self.corp_path / "templates" / "industries"
        self.templates_path.mkdir(parents=True, exist_ok=True)

    def list_templates(self) -> List[str]:
        """List available industry templates"""
        return list(INDUSTRY_TEMPLATES.keys())

    def get_template(self, industry: str) -> Optional[Dict[str, Any]]:
        """Get a specific industry template"""
        return INDUSTRY_TEMPLATES.get(industry)

    def apply_template(
        self,
        industry: str,
        clear_existing: bool = False,
        customize: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply an industry template to configure AI Corp.

        Args:
            industry: Industry template name
            clear_existing: Whether to clear existing org structure
            customize: Optional customizations to the template

        Returns:
            Summary of created structure
        """
        template = self.get_template(industry)
        if not template:
            raise ValueError(f"Unknown industry template: {industry}")

        # Apply customizations
        if customize:
            template = self._merge_customizations(template, customize)

        if clear_existing:
            self._clear_org_structure()

        created = {
            'industry': industry,
            'departments': [],
            'vps': [],
            'directors': [],
            'workers': [],
            'quality_gates': template['quality_gates']
        }

        # Create departments and roles
        for dept in template['departments']:
            # Create VP
            vp = self.hiring.hire_vp(
                role_id=dept['vp'],
                name=f"VP of {dept['name'].replace(' Department', '').replace(' Division', '')}",
                department=dept['id'],
                responsibilities=[
                    f"Lead {dept['name']}",
                    'Receive tasks from COO',
                    'Delegate to directors',
                    'Report progress'
                ]
            )
            created['vps'].append(vp)

            # Create directors
            for dir_def in dept['directors']:
                director = self.hiring.hire_director(
                    role_id=dir_def['id'],
                    name=dir_def['name'],
                    department=dept['id'],
                    reports_to=dept['vp'],
                    focus=dir_def['focus'],
                    responsibilities=[
                        f"Lead {dir_def['focus']}",
                        'Manage worker pool',
                        'Report to VP'
                    ],
                    skills=dir_def.get('skills', []),
                    manages_pool=f"pool_{dir_def['id'].replace('dir_', '')}"
                )
                created['directors'].append(director)

            # Create worker types
            for worker_type in dept.get('worker_types', []):
                worker = self.hiring.hire_worker(
                    role_id=worker_type,
                    name=worker_type.replace('_', ' ').title(),
                    department=dept['id'],
                    pool=f"pool_{worker_type}",
                    director=dept['directors'][0]['id'] if dept['directors'] else dept['vp'],
                    description=f"Executes {worker_type.replace('_', ' ')} tasks",
                    capabilities=[worker_type],
                    responsibilities=[
                        'Execute assigned tasks',
                        'Report progress',
                        'Create checkpoints'
                    ]
                )
                created['workers'].append(worker)

            created['departments'].append(dept['id'])

        # Save template metadata
        self._save_applied_template(industry, template, created)

        print(f"\n[Templates] Applied '{template['name']}' template")
        print(f"  - {len(created['departments'])} departments")
        print(f"  - {len(created['vps'])} VPs")
        print(f"  - {len(created['directors'])} directors")
        print(f"  - {len(created['workers'])} worker types")

        return created

    def create_custom_template(
        self,
        name: str,
        description: str,
        departments: List[Dict[str, Any]],
        quality_gates: List[str],
        molecule_templates: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Create a custom industry template.

        Args:
            name: Template name
            description: Template description
            departments: List of department definitions
            quality_gates: List of quality gate names
            molecule_templates: Optional molecule template names

        Returns:
            The created template
        """
        template_id = name.lower().replace(' ', '_')

        template = {
            'name': name,
            'description': description,
            'departments': departments,
            'quality_gates': quality_gates,
            'molecule_templates': molecule_templates or []
        }

        # Save to file
        template_file = self.templates_path / f"{template_id}.yaml"
        template_file.write_text(yaml.dump(template, default_flow_style=False, sort_keys=False))

        # Add to in-memory templates
        INDUSTRY_TEMPLATES[template_id] = template

        print(f"[Templates] Created custom template: {name}")
        return template

    def _merge_customizations(
        self,
        template: Dict[str, Any],
        customize: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Merge customizations into template"""
        result = template.copy()

        # Add extra departments
        if 'add_departments' in customize:
            result['departments'] = result['departments'] + customize['add_departments']

        # Remove departments
        if 'remove_departments' in customize:
            result['departments'] = [
                d for d in result['departments']
                if d['id'] not in customize['remove_departments']
            ]

        # Add quality gates
        if 'add_gates' in customize:
            result['quality_gates'] = result['quality_gates'] + customize['add_gates']

        return result

    def _clear_org_structure(self) -> None:
        """Clear existing organizational structure"""
        org_path = self.corp_path / "org"

        # Keep hierarchy.yaml base structure
        for subdir in ['departments', 'roles']:
            subpath = org_path / subdir
            if subpath.exists():
                for f in subpath.glob("*.yaml"):
                    # Keep executive.yaml
                    if f.name != 'executive.yaml':
                        f.unlink()

    def _save_applied_template(
        self,
        industry: str,
        template: Dict[str, Any],
        created: Dict[str, Any]
    ) -> None:
        """Save metadata about the applied template"""
        from datetime import datetime

        metadata = {
            'industry': industry,
            'template_name': template['name'],
            'applied_at': datetime.utcnow().isoformat(),
            'summary': {
                'departments': len(created['departments']),
                'vps': len(created['vps']),
                'directors': len(created['directors']),
                'workers': len(created['workers'])
            }
        }

        metadata_file = self.corp_path / "org" / "template_metadata.yaml"
        metadata_file.write_text(yaml.dump(metadata, default_flow_style=False))


def init_corp(corp_path: Path, industry: str = 'software') -> Dict[str, Any]:
    """
    Initialize AI Corp for a specific industry.

    This is the main entry point for setting up a new AI Corp instance.

    Args:
        corp_path: Path to corp directory
        industry: Industry template to use

    Returns:
        Summary of created structure

    Example:
        init_corp(Path('./my-corp'), 'construction')
    """
    manager = IndustryTemplateManager(corp_path)
    return manager.apply_template(industry, clear_existing=True)
