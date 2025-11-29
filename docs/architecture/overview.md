# Atlas.AI Architecture Overview

## Executive Summary

Atlas.AI is an AI-powered location intelligence platform designed to help users explore and analyze geographic data for Delhi, India. The platform combines geospatial data analysis with a conversational AI interface, allowing users to query data using natural language.

## Core Value Proposition

- **Natural Language Queries**: Ask questions like "How many restaurants are in the database?" and get instant results with SQL generation
- **Interactive Map Interface**: Explore Delhi's geographic data through an interactive map with color-coded POI markers
- **Text-to-SQL Pipeline**: Powered by Groq's LLM API for converting natural language to SQL queries
- **Real-time Data Visualization**: Dynamic rendering of areas, pincodes, and points of interest

## System Architecture

### High-Level Stack

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend                                 │
│              React (Vite) + Tailwind CSS + Leaflet              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway                                 │
│                     FastAPI (Python)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   AI Agent      │  │    Database     │  │  Text-to-SQL    │
│   LangChain     │  │     DuckDB      │  │   Groq LLM      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Component Breakdown

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React + Vite + Tailwind | Interactive map UI with chat interface |
| Map Engine | Leaflet + MapLibre GL | Vector tile rendering, POI visualization |
| Backend API | FastAPI | REST endpoints, request handling |
| AI Layer | LangChain + Groq | Natural language processing, SQL generation |
| Database | DuckDB | Spatial data storage and queries |

## Data Model

The platform uses a Delhi-centric geographic data model:

### Tables

| Table | Description | Records |
|-------|-------------|---------|
| `delhi_city` | City boundary polygon | 1 |
| `delhi_area` | District/area boundaries | 11 |
| `delhi_pincode` | Postal code boundaries | 30 |
| `delhi_points` | Points of interest | 200+ |

### POI Categories

- Restaurant, Cafe, Mall, Monument, Market, Hospital, Metro Station

## Key Features

### 1. Chat-with-Map Interface
Users interact with the map through natural language queries in a chat interface.

### 2. Text-to-SQL Pipeline
```
User Question → LLM (Groq) → SQL Generation → Execute on DuckDB → Natural Language Summary
```

### 3. Color-Coded POI Markers
Each category has a distinct color for easy visual identification on the map.

### 4. Interactive Layers
Toggle visibility of different data layers (competitors, heatmaps, areas).

## Technology Stack Summary

### Backend
- **FastAPI**: High-performance Python web framework
- **LangChain**: LLM orchestration and tool integration
- **Groq**: Fast LLM inference for text-to-SQL
- **DuckDB**: Embedded analytical database with spatial support

### Frontend
- **React 19**: Modern UI framework
- **Vite**: Fast build tool
- **Tailwind CSS**: Utility-first styling
- **Leaflet + MapLibre GL**: Map rendering
- **Axios**: HTTP client

### Infrastructure
- **Docker + Docker Compose**: Containerized deployment
- **Nginx**: Frontend static file serving
