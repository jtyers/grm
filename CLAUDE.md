# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

```bash
# Install dependencies
pdm install

# Run the application
./grm [command]

# Run with debug mode
DEBUG=1 ./grm [command]

# Build distribution packages
make build_dist

# Clean build artifacts  
make clean
```

## Architecture

`grm` is a Python CLI tool for managing Git repositories. The main entry point is the `grm` shell script which uses PDM to execute the Python application.

**Core Components:**
- `src/grm/_internal/main.py` - Click-based CLI with three commands: `clone`, `create`, `update`
- `src/grm/config.py` - YAML configuration loading with deep merging of defaults
- `src/grm/path_rules.py` - Path transformation system for organizing repositories into directory structures

**Key Concepts:**
- **Path Rules**: Transform repository URLs into local directory paths using configurable rules (split, delete operations)
- **Path Join Rules**: Reverse transformation for repository creation workflow
- **Configuration**: Uses `~/.config/grm/grm.yaml` with fallback to hardcoded defaults

The `clone` command applies path rules to determine where repositories should be stored relative to a configured `repo_root`. The `create` command works in reverse, using path join rules to determine the repository name from the current directory path.