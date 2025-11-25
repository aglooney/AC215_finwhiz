# FinWhiz Frontend

*Last Updated: November 25, 2024*

A modern React + TypeScript web application for FinWhiz - an AI-powered financial education assistant with live portfolio tracking and market data integration.

## Features

### User Experience
- **Authentication**: Login and signup interfaces (UI implemented, enforcement planned)
- **Onboarding Flow**: Personalized setup with age, retirement goals, and risk tolerance assessment
- **Portfolio Recommendations**: Dynamic asset allocation based on user profile
- **Chat Interface**: Real-time conversation with AI assistant powered by Gemini 2.5
- **Document Upload**: Upload W-2, 1099, and portfolio statements for personalized insights

### Portfolio & Market Features (NEW)
- **Live Portfolio Tracking**: Real-time portfolio valuation with current market prices
- **Market Overview Dashboard**: Live quotes, major indices (S&P 500, Dow, NASDAQ)
- **Gain/Loss Analysis**: Automatic calculation of portfolio performance
- **Market Data Integration**: Access to stock quotes and historical price data

### Design
- **Responsive Design**: Works seamlessly on desktop and mobile devices
- **Modern UI**: Built with Tailwind CSS for a clean, professional look
- **Accessible**: WCAG compliant components with proper ARIA labels

---

## Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.3.1 | UI library |
| **TypeScript** | 5.2.2 | Type safety and IDE support |
| **Vite** | 5.4.8 | Fast build tool and dev server with HMR |
| **Tailwind CSS** | 3.4.1 | Utility-first CSS framework |
| **Axios** | 1.6.7 | HTTP client for API calls |
| **Lucide React** | 0.344.0 | Beautiful, consistent icon library |
| **Nginx** | 1.25 (Alpine) | Production web server and reverse proxy |

---

## Development

### Prerequisites

- **Node.js** 20+ (LTS recommended)
- **npm** 9+ or **yarn** 1.22+
- **Backend services** running (Agent API on 8010, LLM API on 8001)

### Local Development Setup

#### Option 1: Standalone Frontend (Recommended)

```bash
cd src/frontend

# Install dependencies
npm install

# Start development server (requires backend services running)
npm run dev
```

The dev server will run on `http://localhost:3000` with:
- Hot module replacement (HMR) for instant updates
- Automatic TypeScript type checking
- API proxying to backend services

#### Option 2: Full Docker Stack

```bash
# From project root
docker-compose up --build
```

The frontend will be available at `http://localhost:3000`

### Available Scripts

```bash
# Development server with HMR
npm run dev

# Build for production
npm run build

# Preview production build locally
npm run preview

# Type check without building
npm run type-check

# Lint code (ESLint)
npm run lint

# Format code (Prettier)
npm run format
```

---

## Architecture

### Project Structure

```
src/frontend/
├── public/                 # Static assets
│   └── vite.svg           # Favicon
├── src/
│   ├── main.tsx           # React entry point
│   ├── App.tsx            # Root component with routing
│   ├── index.css          # Global styles and Tailwind
│   ├── components/        # Reusable UI components
│   │   ├── Login.tsx              # User login (NEW)
│   │   ├── Signup.tsx             # User registration (NEW)
│   │   ├── ChatInterface.tsx      # Chat UI with message history
│   │   ├── DocumentUpload.tsx     # File upload component
│   │   ├── PortfolioRecommendation.tsx  # Static portfolio allocation
│   │   ├── LivePortfolio.tsx      # Real-time portfolio tracking (NEW)
│   │   └── MarketOverview.tsx     # Market dashboard (NEW)
│   ├── pages/             # Top-level page components
│   │   ├── Onboarding.tsx  # User onboarding wizard
│   │   └── Dashboard.tsx   # Main application layout
│   ├── services/          # API clients and utilities
│   │   └── api.ts         # Backend API integration
│   ├── contexts/          # React contexts (NEW)
│   │   └── AuthContext.tsx  # Authentication state (planned)
│   └── types/             # TypeScript type definitions
│       └── index.ts       # Shared types and interfaces
├── Dockerfile             # Multi-stage production build
├── nginx.conf             # Production server configuration
├── vite.config.ts         # Vite configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── tsconfig.json          # TypeScript configuration
├── package.json           # Dependencies and scripts
└── README.md              # This file
```

---

## Components

### Authentication (NEW)

#### Login.tsx
- Email and password input
- Form validation
- Error handling
- Redirect to dashboard on success

**Status**: UI implemented, authentication enforcement planned for Milestone 5

#### Signup.tsx
- User registration form
- Password confirmation
- Terms of service acceptance
- Account creation flow

**Status**: UI implemented, backend integration planned

---

### Pages

#### Onboarding.tsx
Two-step wizard for new users:

**Step 1: Profile Information**
- Current age input
- Target retirement age input
- Investment goals text area

**Step 2: Risk Assessment**
- Risk tolerance selector (Conservative, Moderate, Aggressive)
- Asset allocation preview

**State Management**: localStorage for persistence

#### Dashboard.tsx
Main application interface with:
- Tabbed navigation (Chat, Upload, Portfolio, Market)
- User profile sidebar
- Session management
- Responsive layout

---

### Core Components

#### ChatInterface.tsx
Real-time AI conversation interface:

**Features**:
- Message history display
- User and assistant message styling
- Source citations with relevance scores
- Loading states during query processing
- Error handling
- Auto-scroll to latest message

**API Integration**:
- POST `/api/llm/query` - Submit questions
- Session context automatically included

#### DocumentUpload.tsx
File upload interface for financial documents:

**Supported Types**:
- W-2 forms
- 1099 forms
- Portfolio statements

**Features**:
- Drag-and-drop file selection
- Document type selector
- Upload progress indicators
- Success/error notifications
- Extracted data display
- Upload history

**API Integration**:
- POST `/api/agent/sessions/{id}/w2`
- POST `/api/agent/sessions/{id}/1099`
- POST `/api/agent/sessions/{id}/portfolio`

#### PortfolioRecommendation.tsx
Static portfolio allocation recommendations:

**Calculations**:
- Stock percentage: 100 - age (adjusted for risk)
- Bond percentage: age (adjusted for risk)
- Cash reserve: 5-15% based on risk tolerance

**Display**:
- Visual progress bars
- Percentage breakdowns
- Years to retirement
- Risk-adjusted allocations

---

### Market Features (NEW)

#### LivePortfolio.tsx
Real-time portfolio tracking with live market data:

**Features**:
- Current portfolio value
- Individual holding performance
- Real-time price updates
- Gain/loss calculations ($ and %)
- Color-coded performance indicators
- Total portfolio metrics

**Data Source**: Yahoo Finance via Agent API

**API Integration**:
- GET `/api/agent/sessions/{id}/portfolio/live`

**Display**:
- Holdings table with current prices
- Gain/loss indicators (green/red)
- Total value and performance summary
- Last updated timestamp

**Requirements**: Portfolio statement must be uploaded first

#### MarketOverview.tsx
Market dashboard with indices and quotes:

**Features**:
- Major indices (S&P 500, Dow Jones, NASDAQ)
- Real-time index values and changes
- Stock quote lookup
- Historical price charts (planned)
- Market trend indicators

**API Integration**:
- GET `/api/agent/market/indices` - Major indices
- GET `/api/agent/market/quote/{ticker}` - Individual stocks
- GET `/api/agent/market/history/{ticker}` - Historical data

**Display**:
- Index cards with current values
- Change indicators with color coding
- Search bar for stock quotes
- Refresh button for manual updates

---

## API Integration

The frontend communicates with two backend services via Nginx proxy:

### 1. Agent API (`/api/agent/*` → `http://agent:8010`)

#### Session Management
- `POST /sessions/` - Create new session
- `POST /sessions/{id}/messages` - Add message to session
- `GET /sessions/{id}/context` - Get full session context

#### Document Upload
- `POST /sessions/{id}/w2` - Upload W-2 form (PDF)
- `POST /sessions/{id}/1099` - Upload 1099 form (PDF)
- `POST /sessions/{id}/portfolio` - Upload portfolio statement (PDF)

#### Portfolio Features (NEW)
- `GET /sessions/{id}/portfolio/live` - Real-time portfolio values
- `GET /sessions/{id}/portfolio/analytics` - Portfolio analysis

#### Market Data (NEW)
- `GET /market/quote/{ticker}` - Stock quote
- `GET /market/indices` - Major indices
- `GET /market/history/{ticker}` - Historical prices

### 2. LLM API (`/api/llm/*` → `http://llm:8001`)

- `POST /query` - Submit query and get AI response with RAG
- `GET /health` - Service health check

### API Client (`src/services/api.ts`)

Centralized API client with:
- Axios instance configuration
- Base URL handling (development vs. production)
- Request/response interceptors
- Error handling
- TypeScript types for all endpoints

**Example Usage**:
```typescript
import { createSession, queryLLM, getStockQuote } from './services/api';

// Create session
const session = await createSession('user-123');

// Query LLM
const response = await queryLLM({
  query: 'What is a Roth IRA?',
  session_id: session.session_id,
  top_k: 5
});

// Get stock quote
const quote = await getStockQuote('AAPL');
```

---

## State Management

### Local State
- React `useState` for component-specific state
- Form inputs, UI toggles, loading states

### Session Persistence
- `localStorage` for session ID
- User profile data (age, retirement goals, risk tolerance)
- Persistent across page refreshes

### Planned Enhancements
- React Context for global state (authentication)
- Redux or Zustand for complex state management
- Server-side session management with JWT

---

## Styling

### Tailwind CSS

Utility-first CSS framework for rapid development:

```typescript
<button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
  Submit
</button>
```

### Custom Styles

Global styles in `src/index.css`:
- Tailwind base, components, utilities
- Custom scrollbar styling
- Typography defaults
- Animation keyframes

### Responsive Design

Mobile-first approach with Tailwind breakpoints:
- `sm:` 640px
- `md:` 768px
- `lg:` 1024px
- `xl:` 1280px
- `2xl:` 1536px

---

## Environment Configuration

### Development
API requests proxied via Vite dev server (`vite.config.ts`):
```typescript
server: {
  proxy: {
    '/api/agent': 'http://localhost:8010',
    '/api/llm': 'http://localhost:8001',
  }
}
```

### Production
API requests proxied via Nginx (`nginx.conf`):
```nginx
location /api/agent/ {
    proxy_pass http://agent:8010/;
}

location /api/llm/ {
    proxy_pass http://llm:8001/;
}
```

No environment variables needed in the frontend - all configuration handled server-side.

---

## Docker Deployment

### Multi-Stage Build

```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Serve
FROM nginx:1.25-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx Configuration

Features:
- API reverse proxying
- Gzip compression
- Cache headers for static assets
- SPA fallback routing (try_files)
- Health check endpoint

---

## Production Build

The production build process:

1. **TypeScript Compilation**: `.tsx` → `.js`
2. **Asset Bundling**: Modules bundled with Vite/Rollup
3. **Minification**: JavaScript and CSS minified
4. **Optimization**: Tree shaking, code splitting
5. **Static Generation**: Optimized files output to `/dist`
6. **Nginx Serving**: Static assets + API proxying

**Build Artifacts**:
```
dist/
├── index.html          # Entry point
├── assets/
│   ├── index-[hash].js     # Bundled JavaScript
│   ├── index-[hash].css    # Bundled CSS
│   └── vite.svg            # Static assets
└── ...
```

---

## Browser Support

**Recommended Browsers**:
- Chrome/Edge 90+ (latest recommended)
- Firefox 88+ (latest recommended)
- Safari 14+ (latest recommended)

**Features Used**:
- ES2020+ JavaScript
- CSS Grid and Flexbox
- Fetch API
- LocalStorage
- Web Animations API

---

## Testing

### Manual Testing Checklist

**Authentication** (UI only):
- [ ] Login form displays correctly
- [ ] Signup form displays correctly
- [ ] Form validation works

**Onboarding**:
- [ ] Step 1: Age and retirement inputs work
- [ ] Step 2: Risk tolerance selection works
- [ ] Portfolio recommendations display correctly
- [ ] Data persists in localStorage

**Chat**:
- [ ] Messages send and display
- [ ] AI responses appear with sources
- [ ] Loading states show correctly
- [ ] Error handling works

**Document Upload**:
- [ ] File selection works (drag & drop and click)
- [ ] Document type selector works
- [ ] Upload progress displays
- [ ] Extracted data shows after upload
- [ ] Multiple documents can be uploaded

**Live Portfolio**:
- [ ] Displays after portfolio upload
- [ ] Shows current prices and values
- [ ] Calculates gains/losses correctly
- [ ] Updates on refresh

**Market Overview**:
- [ ] Indices display with current values
- [ ] Stock quote search works
- [ ] Data refreshes correctly

### Automated Testing (Planned)

- **Unit Tests**: Jest + React Testing Library
- **E2E Tests**: Playwright or Cypress
- **Component Tests**: Storybook

---

## Performance

### Optimizations

- **Code Splitting**: Lazy loading for routes
- **Asset Optimization**: Image compression, font subsetting
- **Bundle Analysis**: Vite build analyzer
- **Caching**: Aggressive caching for static assets
- **Compression**: Gzip/Brotli in Nginx

### Metrics

Target performance:
- First Contentful Paint (FCP): < 1.5s
- Largest Contentful Paint (LCP): < 2.5s
- Time to Interactive (TTI): < 3.5s
- Cumulative Layout Shift (CLS): < 0.1

---

## Contributing

When adding new features:

1. **Components**: Create in `/src/components` with descriptive names
2. **Pages**: Add in `/src/pages` for top-level routes
3. **Types**: Update `/src/types/index.ts` with new interfaces
4. **API Methods**: Add to `/src/services/api.ts` with proper typing
5. **Styles**: Use Tailwind utilities, create custom classes only when necessary
6. **Documentation**: Update this README when adding major features

### Code Style

- **TypeScript**: Strict mode enabled
- **React**: Functional components with hooks
- **Formatting**: Prettier with 2-space indentation
- **Linting**: ESLint with React and TypeScript rules
- **Naming**: PascalCase for components, camelCase for functions/variables

---

## Troubleshooting

### Dev Server Won't Start

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### API Calls Failing

1. Check backend services are running:
   ```bash
   curl http://localhost:8010/health
   curl http://localhost:8001/health
   ```

2. Check Vite proxy configuration in `vite.config.ts`

3. Check browser console for CORS errors

### Build Errors

```bash
# Type check
npm run type-check

# Clear cache and rebuild
rm -rf dist node_modules/.vite
npm run build
```

### Docker Issues

```bash
# Rebuild without cache
docker-compose build --no-cache frontend

# Check logs
docker logs finwhiz_frontend -f
```

---

## Related Documentation

- **Main README**: [../../README.md](../../README.md)
- **Development Guide**: [../../docs/DEVELOPMENT.md](../../docs/DEVELOPMENT.md)
- **API Reference**: [../../docs/API_REFERENCE.md](../../docs/API_REFERENCE.md)
- **Architecture**: [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md)

---

*For detailed development setup and troubleshooting, see the main [Development Guide](../../docs/DEVELOPMENT.md).*
