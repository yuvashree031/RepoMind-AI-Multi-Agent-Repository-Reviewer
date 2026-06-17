# RepoMind AI

RepoMind AI is an automated repository auditing platform that combines a FastAPI backend with a Next.js frontend. It uses AI-driven agents to analyze source code repositories for security vulnerabilities, code quality issues, architecture insights, and DevOps best practices.

## Project Overview

The project is divided into two main parts:

- `backend/`: A FastAPI service that handles authentication, repository analysis workflows, data storage, and report generation.
- `frontend/`: A Next.js application that provides a login flow, repository submission interface, analysis progress tracking, and detailed audit reports.

RepoMind AI is designed to support both public and private GitHub repositories. Private repositories can be accessed using a personal access token.

## Key Features

- User authentication and session management
- Repository URL submission for automated audit
- Multi-agent workflow for code quality, security, architecture, and DevOps scanning
- Real-time analysis progress tracking
- Detailed review dashboard with scores and findings
- Generated markdown report for completed reviews
- Architecture diagram rendering using Mermaid syntax

## Architecture

The backend starts a FastAPI application and connects to MongoDB. It defines repositories for users, reviews, reports, and analysis history. On each analysis request, it launches a multi-agent workflow that clones the target repository, inspects the codebase, computes scores, and generates a textual report.

The frontend is built with Next.js and provides the following pages:

- Login page for user sign-in
- Dashboard page for starting new audits and viewing past review history
- Analyze page for live progress polling while the analysis executes
- Review detail page to inspect final audit results and generated report

## Running the Project

You can run the project using the existing Docker Compose configuration located at `infrastructure/docker/docker-compose.yml`, or run the backend and frontend separately.

### Backend

Install Python dependencies from `backend/requirements.txt` and start the FastAPI app. The backend exposes endpoints for authentication, review submission, and review status.

### Frontend

Install npm dependencies in `frontend/` and start the Next.js dev server with `npm run dev` or `yarn dev`.

## Screenshots

The following images demonstrate the project flow and features.

### 1. Sign In

![Sign In](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/sign.png)

### 2. Register

![Register](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/register.png)

### 3. Dashboard

![Dashboard](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/dashboard.png)

### 4. Analyze

![Analyze](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/analyze.png)

### 5. Summary

![Summary](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/summary.png)

### 6. Language Detection

![Language Detection](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/language.png)

### 7. Code Quality

![Code Quality](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/code.png)

### 8. Architecture Map

![Architecture Map](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/map.png)

### 9. DevOps Review

![DevOps Review](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/devOps.png)

### 10. Full Report

![Full Report](https://raw.githubusercontent.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/master/RepoMind%20AI%20-%20images/full_report.png)

## Demo Video

The following video demonstrates RepoMind AI in action, including the multi-agent review workflow.

[▶ RepoMind AI – Multi-Agent Repository Reviewer](https://github.com/yuvashree031/RepoMind-AI-Multi-Agent-Repository-Reviewer/blob/master/RepoMind%20AI%20-%20images/RepoMind%20AI%20%E2%80%93%20Multi-Agent%20Repository%20Reviewer.mp4)

## Notes

- The backend uses MongoDB for data persistence.
- The frontend is configured with Tailwind CSS and TypeScript.
- The repository uses agent-driven workflows to orchestrate analysis tasks.
