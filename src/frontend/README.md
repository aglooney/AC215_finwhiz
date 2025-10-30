# FinWhiz Frontend

A modern React + TypeScript web application for FinWhiz - an AI-powered financial education assistant.

## Features

- **Onboarding Flow**: Collects user age, retirement goals, and risk tolerance
- **Portfolio Recommendations**: Personalized asset allocation based on user profile
- **Chat Interface**: Real-time conversation with AI assistant powered by Gemini 2.5
- **Document Upload**: Upload W-2 and 1099 forms for personalized insights
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Fast build tool and dev server
- **Tailwind CSS** - Utility-first CSS framework
- **Axios** - HTTP client for API calls
- **Lucide React** - Beautiful icon library
- **Nginx** - Production web server

## Development

### Prerequisites

- Node.js 20+
- npm or yarn

### Local Development

```bash
cd src/frontend

# Install dependencies
npm install

# Start development server (requires backend services running)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

The dev server will run on `http://localhost:3000` and proxy API requests to the backend services.

## Docker Deployment

The frontend is containerized and deployed via Docker Compose:

```bash
# From project root
docker-compose up --build frontend
```

The frontend will be available at `http://localhost:3000`

## Architecture

### Components

- **Onboarding** (`/src/pages/Onboarding.tsx`) - User onboarding wizard
- **Dashboard** (`/src/pages/Dashboard.tsx`) - Main application layout
- **ChatInterface** (`/src/components/ChatInterface.tsx`) - Chat UI with message history
- **DocumentUpload** (`/src/components/DocumentUpload.tsx`) - File upload component
- **PortfolioRecommendation** (`/src/components/PortfolioRecommendation.tsx`) - Portfolio visualization

### API Integration

The frontend communicates with two backend services:

1. **Agent API** (`/api/agent`) - Session management and document processing
   - POST `/sessions/` - Create new session
   - POST `/sessions/{id}/messages` - Add message
   - POST `/sessions/{id}/w2` - Upload W-2
   - POST `/sessions/{id}/1099` - Upload 1099
   - GET `/sessions/{id}/context` - Get session context

2. **LLM API** (`/api/llm`) - Query processing with RAG
   - POST `/query` - Submit query and get AI response

### State Management

- Local React state for UI interactions
- localStorage for session persistence
- Session ID passed to all API calls for context

## Environment Variables

No environment variables needed for the frontend. API endpoints are proxied via Nginx in production and Vite dev server in development.

## Production Build

The production build:
1. Compiles TypeScript to JavaScript
2. Bundles and minifies assets
3. Generates optimized static files in `/dist`
4. Serves via Nginx with API proxying

## Browser Support

- Chrome/Edge (latest)
- Firefox (latest)
- Safari (latest)

## Contributing

When adding new features:
1. Create new components in `/src/components`
2. Add new pages in `/src/pages`
3. Update types in `/src/types/index.ts`
4. Add API methods in `/src/services/api.ts`
5. Follow existing code style and patterns
