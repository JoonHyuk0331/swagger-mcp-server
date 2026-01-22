# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based MCP (Model Context Protocol) server for working with Swagger/OpenAPI specifications. The project uses `uv` as the Python package manager.

## Development Setup

**Python Version**: 3.9+ (specified in `.python-version`)

**Package Manager**: uv

Install dependencies:
```bash
uv pip install -e .
```

## Project Structure

Currently in early initialization stage. The main entry point is `main.py`, which contains placeholder code that should be replaced with the MCP server implementation.

## Architecture Notes

This project is intended to be an MCP server that:
- Exposes tools for interacting with Swagger/OpenAPI specifications
- Allows Claude to read, parse, and query API documentation
- Potentially generates API client code or validates API schemas

The server should follow the MCP protocol specification for tool registration and execution.
