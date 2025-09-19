# Research Agent Frontend - Claude Development Notes

## Project Overview
This is a Next.js 15.5.3 application using TypeScript, React, and shadcn/ui components for an AI-powered research assistant frontend.

## Recent Modernization (2025-09-18)

### UI Enhancements Completed
1. **Modern Sidebar Navigation**
   - Added collapsible sidebar with recent research history
   - Quick access navigation menu
   - Settings and help links in footer

2. **Theme Support**
   - Dark mode implementation with next-themes
   - System preference detection
   - Smooth theme transitions

3. **Hero Summary Tab**
   - Gradient hero section with stats cards
   - Processing time, sources analyzed metrics
   - Magazine-style typography for executive summaries

4. **Professional App Shell**
   - Modern layout with SidebarProvider
   - Header with sidebar trigger and theme toggle
   - Responsive design with mobile support

### File Structure
```
components/
  app-sidebar.tsx         # Main sidebar navigation component
  theme-toggle.tsx        # Dark/light mode toggle
  providers/
    theme-provider.tsx    # Next-themes provider wrapper
  research/
    hero-summary.tsx      # Modern hero section for summary tab
    analysis-section.tsx  # Fixed markdown rendering with magazine typography
    research-results.tsx  # Main results component using HeroSummary
    research-results.module.css  # Magazine-style typography CSS

app/
  layout.tsx             # Updated with sidebar and theme provider integration
```

### Known Issues & Notes
- The sidebar may not appear on initial load if hot reload doesn't pick up layout changes
- Dev server runs on port 3001 (port 3000 is occupied by another service)
- Markdown rendering in detailed analysis sections has been fixed to properly parse bold, italic, and other formatting
- **IMPORTANT**: The parent CLAUDE.md recommends using containerized environment to avoid React Query cache issues

### Development Commands
```bash
# Install dependencies
npm install

# Run development server locally (not recommended - see parent CLAUDE.md)
npm run dev
# The app will be available at http://localhost:3001

# Recommended: Use Docker Compose from parent directory
cd ..
docker-compose up --build -d
# Access containerized frontend (avoids React Query cache issues)
```

### Key Dependencies
- Next.js 15.5.3 with Turbopack
- shadcn/ui components
- next-themes for dark mode
- Tailwind CSS for styling
- TypeScript for type safety

### Recent Fixes
1. Fixed markdown content rendering that was showing literal quoted strings
2. Fixed CSS syntax error in blockquote pseudo-elements
3. Implemented aggressive quote removal in formatContent function
4. Added comprehensive markdown pattern detection

### Testing
To test the modernized UI:
1. Navigate to http://localhost:3001
2. Check sidebar toggle functionality
3. Test theme toggle (light/dark mode)
4. View a research report to see the new Summary tab with hero section
5. Verify markdown formatting in Detailed Analysis sections

### Future Improvements
- Add skeleton loaders during data fetching
- Implement command palette (⌘K) for quick navigation
- Add more animations with Framer Motion
- Modernize Sources tab with masonry grid layout
- Add charts and data visualizations for findings