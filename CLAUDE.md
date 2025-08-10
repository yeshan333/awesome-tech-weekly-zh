# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a curated collection of Chinese technical weekly newsletters across various technology domains. The repository automatically generates a README.md file from YAML configuration files using GitHub Actions.

## Code Architecture and Structure

- `/items/` - Contains YAML files organized by technology category (AI, Go, Python, etc.)
- `/template/` - Contains templates for generating README files
- `/resources/` - Contains English version of README
- `.github/workflows/` - GitHub Actions for automatic README generation

Each YAML file in `/items/` follows this structure:
```yaml
kind: [Category]
owner: [Owner Name]
name: '[Newsletter Name]'
link: [Website URL]
desc: '[Description in Chinese]'
desc_en: '[Description in English]'
feed_url: [RSS/Atom feed URL]
```

## Common Development Tasks

### Adding a New Newsletter
1. Create a new YAML file in the appropriate category directory under `/items/`
2. Follow the existing YAML structure
3. Commit and push - the README will be automatically updated by GitHub Actions

### Adding a New Category
1. Create a new directory under `/items/` with the category name
2. Add YAML files for newsletters in that category
3. The new category will automatically appear in the README

### Modifying Existing Newsletters
1. Edit the appropriate YAML file in `/items/[category]/`
2. Changes will be reflected in the next automated README update

## Build and Deployment

The repository uses GitHub Actions to automatically update the README daily:
- Workflow: `.github/workflows/readme-generator.yml`
- Runs daily at midnight UTC
- Uses the `yeshan333/yaml-readme` GitHub Action
- Reads all YAML files in `items/*/*.yaml`
- Generates README.md from `template/README.tpl`

## Testing

To test changes locally:
1. Make changes to YAML files
2. Run the yaml-readme tool locally (if available)
3. Or wait for the scheduled GitHub Action to run

The repository is automatically updated daily, so manual intervention is rarely needed.