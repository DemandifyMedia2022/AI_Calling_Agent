# AI Calling Agent - React Frontend

A modern React frontend for the AI Calling Agent with TypeScript, Tailwind CSS, and Shadcn/UI components.

## 🚀 Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+ (for backend)
- Your existing FastAPI backend running

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install
```

### 2. Start the Development Servers

**Terminal 1 - Backend (FastAPI):**
```bash
# From the root directory
uvicorn webui.app:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend (React):**
```bash
# From the frontend directory
cd frontend
npm run dev
```

The React app will be available at: **http://localhost:3000**

The Vite dev server automatically proxies API calls to your FastAPI backend at port 8000.

## 🛠️ Technology Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **Shadcn/UI** for beautiful components
- **React Router** for navigation
- **React Query** for API state management
- **Lucide React** for icons

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/          # Reusable UI components
│   │   ├── ui/             # Shadcn/UI components
│   │   ├── Header.tsx      # Top navigation
│   │   ├── Sidebar.tsx     # Side navigation
│   │   ├── Layout.tsx      # Main layout wrapper
│   │   ├── CampaignSelector.tsx
│   │   ├── StatusPanel.tsx
│   │   ├── CurrentCallCard.tsx
│   │   └── LeadsTable.tsx
│   ├── pages/              # Main application pages
│   │   ├── Dashboard.tsx   # Main dashboard
│   │   ├── CsvManager.tsx  # CSV file management
│   │   └── CampaignsManager.tsx # Campaign editor
│   ├── hooks/              # Custom React hooks
│   │   ├── useApiStatus.ts # Real-time status polling
│   │   ├── useLeads.ts     # Leads data management
│   │   └── useCampaigns.ts # Campaigns data
│   ├── lib/                # Utilities and API client
│   │   ├── api.ts          # API client functions
│   │   └── utils.ts        # Helper functions
│   ├── types/              # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx             # Main app component
│   ├── main.tsx            # App entry point
│   └── index.css           # Global styles
├── package.json
├── vite.config.ts          # Vite configuration
├── tailwind.config.js      # Tailwind configuration
├── components.json         # Shadcn/UI configuration
└── tsconfig.json           # TypeScript configuration
```

## 🎨 Features

### Dashboard
- **Campaign Selection**: Choose from built-in or custom campaigns
- **Real-time Status**: Live polling of call status and details
- **Call Controls**: Start calls, end calls, auto-next functionality
- **Live Call Card**: Shows current call details when active
- **Leads Table**: Paginated view of prospects with inline call buttons

### CSV Manager
- **File Upload**: Drag & drop or select CSV files
- **File Management**: View, preview, download, and delete CSV files
- **Active File Selection**: Set which CSV file is currently active
- **Live Preview**: See CSV contents before selection

### Campaigns Manager
- **Campaign Editor**: Create and edit campaign prompts
- **Template Management**: Built-in and custom campaign templates
- **File Upload**: Upload agent and session instructions from text files
- **Supabase Integration**: Sync campaigns to cloud database

## 🔧 Configuration

### Environment Variables

The React app uses the backend's environment variables through API proxying. Ensure your `.env` file in the root directory contains:

```env
# LiveKit server
LIVEKIT_URL=wss://your-livekit-host
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# Optional: path to leads CSV
LEADS_CSV_PATH=d:/path/to/leads.csv

# Campaign configuration
CAMPAIGN_PROMPT_MODULE=prompts
CAMPAIGN_AGENT_NAME=ENHANCED_DEMANDIFY_CALLER_INSTRUCTIONS
CAMPAIGN_SESSION_NAME=SESSION_INSTRUCTION

# Optional: Supabase integration
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_service_key
```

### API Proxy Configuration

Vite automatically proxies these routes to the FastAPI backend:

- `/api/*` → `http://localhost:8000/api/*`
- `/vendor/*` → `http://localhost:8000/vendor/*`
- `/browser/*` → `http://localhost:8000/browser/*`

## 🏗️ Building for Production

```bash
cd frontend
npm run build
```

This creates a `dist/` folder with optimized static files.

### Serving the Production Build

```bash
npm run preview
```

Or serve the `dist/` folder with any static file server.

## 🔄 API Integration

The React frontend communicates with your existing FastAPI backend through these endpoints:

### Core APIs (Existing)
- `GET /api/status` - Real-time call status
- `POST /api/start_call` - Start a call
- `POST /api/end_call` - End current call
- `POST /api/select_campaign` - Set active campaign
- `POST /api/auto_next` - Toggle auto-next calls
- `POST /api/stop_all` - End session

### CSV Management (Existing)
- `GET /api/csv/list` - List CSV files
- `POST /api/csv/upload` - Upload CSV file
- `POST /api/csv/select` - Set active CSV
- `DELETE /api/csv/{name}` - Delete CSV file
- `GET /api/csv/preview` - Preview CSV contents

### Campaigns Management (Existing)
- `GET /api/campaigns/list` - List campaigns
- `POST /api/campaigns/create` - Create campaign
- `GET /api/campaigns/get` - Get campaign details
- `POST /api/campaigns/update` - Update campaign
- `DELETE /api/campaigns/{module}` - Delete campaign

### New APIs (Added)
- `GET /api/leads` - Get paginated leads data
- `GET /api/campaigns` - Get campaigns for dropdown

## 🎯 Key Features

### Real-time Updates
- Status polling every second
- Automatic UI updates when calls start/end
- Live call details display

### Modern UX
- Toast notifications for user feedback
- Loading states and error handling
- Responsive design for all screen sizes
- Dark theme optimized for call center usage

### Campaign Management
- Visual campaign editor with syntax highlighting
- File upload for bulk prompt import
- Built-in and custom campaign templates

### CSV Workflow
- Drag & drop file uploads
- Live preview before activation
- File management with metadata display

## 🐛 Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure FastAPI backend is running on port 8000
   - Check that proxy configuration in `vite.config.ts` is correct

2. **TypeScript Errors**
   - Run `npm install` to ensure all dependencies are installed
   - Check that all imported modules exist

3. **Styling Issues**
   - Ensure Tailwind CSS is properly configured
   - Check that all Shadcn/UI components are installed

4. **Build Failures**
   - Clear `node_modules` and reinstall: `rm -rf node_modules && npm install`
   - Check TypeScript configuration in `tsconfig.json`

### Performance Optimization

- React Query caches API responses for better performance
- Debounced search and filtering
- Lazy loading for heavy components
- Optimized re-renders with proper React patterns

## 📱 Browser Support

- Chrome 90+ (recommended for best performance)
- Firefox 88+
- Safari 14+
- Edge 90+

## 🚀 Deployment

### Development
```bash
# Backend
uvicorn webui.app:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm run dev
```

### Production
```bash
# Build frontend
cd frontend && npm run build

# Serve with reverse proxy (nginx example):
# / → React build files
# /api/* → FastAPI backend
# /vendor/* → FastAPI backend
# /browser/* → FastAPI backend
```

Your React frontend is now ready to run! 🎉