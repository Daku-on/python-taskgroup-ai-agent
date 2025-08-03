# AI Agent Dashboard Frontend

React TypeScript frontend for the Python TaskGroup AI Agent system.

## Tech Stack

- **React 19** - Modern React with TypeScript
- **TanStack Router** - Type-safe routing 
- **TanStack Query** - Server state management
- **Jotai** - Atomic state management
- **Tailwind CSS** - Utility-first CSS framework
- **Lucide React** - Beautiful icons
- **Vite** - Fast development server

## Features

- 🤖 **Agent Management** - Execute tasks with different AI agents (LLM, Database, RAG)
- 📊 **Real-time Monitoring** - Live service status and performance metrics
- 🔄 **WebSocket Updates** - Real-time notifications and status updates
- 📋 **Task History** - Track and filter task execution history
- 💾 **Service Dashboard** - Monitor service health and metrics
- 🎯 **Type Safety** - Full TypeScript support throughout

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

### Environment Variables

Create a `.env` file in the frontend directory:

```bash
VITE_API_URL=http://localhost:8000
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Architecture

### State Management

- **Jotai** for client-side state (UI state, filters, selections)
- **TanStack Query** for server state (API data, caching, synchronization)

### Routing

- **TanStack Router** provides type-safe routing with:
  - `/` - Dashboard overview
  - `/tasks` - Task execution interface
  - `/services` - Service monitoring
  - `/monitoring` - Real-time system monitoring

### Real-time Updates

- WebSocket connection for live updates
- Automatic reconnection with exponential backoff
- Toast notifications for system events

### API Integration

- Axios-based HTTP client
- Type-safe API interfaces
- Error handling and retry logic

## Usage

### Executing Tasks

1. Navigate to `/tasks`
2. Select agent type (LLM, Database, or RAG)
3. Enter task name and optional JSON data
4. Click "Execute Task"
5. Monitor progress in task history

### Monitoring Services

1. Navigate to `/services` to view service status
2. Use `/monitoring` for real-time system metrics
3. Filter and search services
4. View performance metrics and health status

### Real-time Updates

- Connection status indicator in dashboard
- Automatic notifications for task completion
- Live service metrics updates
- WebSocket reconnection handling

## Development

### Project Structure

```
src/
├── api/           # API client and WebSocket
├── components/    # Reusable components  
├── hooks/         # Custom hooks
├── routes/        # TanStack Router routes
├── stores/        # Jotai atoms
└── types/         # TypeScript interfaces
```

### Adding New Features

1. Define types in `src/types/`
2. Create API endpoints in `src/api/`
3. Add Jotai atoms in `src/stores/`
4. Build components in `src/components/`
5. Create routes in `src/routes/`

## Backend Integration

This frontend connects to the Python TaskGroup AI Agent backend:

- FastAPI server on http://localhost:8000
- WebSocket endpoint for real-time updates
- RESTful APIs for task execution and monitoring

Make sure the backend server is running before starting the frontend.
