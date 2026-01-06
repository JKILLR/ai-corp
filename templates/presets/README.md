# AI Corp Presets

Industry-specific configurations for AI Corp deployments.

## Available Presets

| Preset | Industry | Description |
|--------|----------|-------------|
| `software-company` | Software | Full-featured software development corporation |
| `_blank` | Generic | Minimal template for creating new presets |

## Using Presets

```bash
# Initialize a new project with a preset
ai-corp init --preset=software-company --name="My Dev Studio" ~/projects/my-studio

# Initialize with the blank template
ai-corp init --preset=_blank --name="My Corp" ~/projects/my-corp
```

## Preset Structure

Each preset follows this structure:

```
presets/{preset-name}/
├── preset.yaml           # Preset manifest and metadata
├── org/                  # Organizational structure
│   ├── hierarchy.yaml    # Reporting chains and levels
│   ├── roles/            # Role definitions
│   │   ├── executive.yaml
│   │   ├── vp.yaml       # (if applicable)
│   │   ├── director.yaml # (if applicable)
│   │   └── worker.yaml
│   └── departments/      # Department configurations
│       └── *.yaml
├── workflows/            # Workflow templates
│   └── *.yaml
├── skills/               # AI skills/tools
│   └── {skill-name}/
│       └── SKILL.md
├── gates/                # Quality gate definitions
│   └── *.yaml
└── config/               # Configuration files
    ├── branding.yaml     # Identity and theming
    ├── models.yaml       # AI model assignments
    └── capabilities.yaml # Capability definitions
```

## Creating New Presets

1. Copy the `_blank` preset:
   ```bash
   cp -r templates/presets/_blank templates/presets/my-industry
   ```

2. Edit `preset.yaml`:
   - Set unique `id` and `name`
   - Update `metadata.industry`
   - Define `includes` list

3. Customize organizational structure:
   - Define hierarchy levels
   - Create roles appropriate for the industry
   - Set up departments

4. Add industry-specific workflows

5. Create quality gates relevant to the domain

6. Update configuration:
   - Branding for the industry
   - Model assignments
   - Capability definitions

## Preset Guidelines

### Hierarchy Design
- Keep hierarchy as flat as practical
- Each level should have clear responsibilities
- Don't add management layers without purpose

### Role Design
- Roles should map to real industry positions
- Define clear responsibilities for each role
- Assign appropriate model tiers

### Workflow Design
- Map common industry processes
- Include quality gates at decision points
- Allow parallel execution where possible

### Gate Design
- Gates should prevent real problems
- Don't add bureaucracy for its own sake
- Automated checks preferred over manual

## Contributing

To contribute a new industry preset:

1. Research the industry thoroughly
2. Create preset following the structure above
3. Test with mock backend
4. Document industry-specific considerations
5. Submit for review
