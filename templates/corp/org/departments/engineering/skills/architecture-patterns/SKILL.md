---
name: architecture-patterns
description: Apply software architecture patterns and best practices. Use when designing system architecture, making technical decisions, or reviewing architectural proposals.
---

# Architecture Patterns Skill

## Overview

This skill provides guidance on software architecture patterns used within Engineering.

## Core Patterns

### Layered Architecture
```
Presentation → Business Logic → Data Access → Database
```
- Each layer only talks to adjacent layers
- Promotes separation of concerns

### Microservices
- Small, independently deployable services
- Each service owns its data
- Communicate via APIs or events

### Event-Driven
- Components communicate through events
- Loose coupling
- Good for async workflows

## Decision Framework

When choosing patterns, consider:
1. **Scale** - How much will this grow?
2. **Team** - Who will maintain this?
3. **Complexity** - Is this pattern justified?
4. **Existing** - What patterns are already in use?

## Anti-Patterns to Avoid

- Big Ball of Mud (no structure)
- Golden Hammer (one pattern for everything)
- Premature optimization
- Over-engineering
