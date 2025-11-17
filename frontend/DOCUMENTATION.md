# TrueSight React Frontend Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Setup & Installation](#setup--installation)
5. [Design System](#design-system)
6. [API Integration](#api-integration)
7. [Components](#components)
8. [Pages](#pages)
9. [Routing](#routing)
10. [Features](#features)
11. [Error Handling](#error-handling)
12. [Deployment](#deployment)

---

## Project Overview

**TrueSight** is a deepfake detection system frontend built with React. It provides a user-friendly interface for uploading videos, monitoring analysis progress, and viewing detection results with visual explanations through Grad-CAM heatmaps.

### Key Features
- Video upload with drag-and-drop support
- Real-time processing status monitoring
- Comprehensive results visualization
- Multi-model ensemble predictions
- Grad-CAM explainability visualizations
- Responsive design (mobile, tablet, desktop)
- Cyberpunk-themed UI with red accent colors

---

## Technology Stack

### Core Technologies
- **React 18.3.1** - UI framework
- **TypeScript** - Type safety
- **Vite** - Build tool and dev server
- **React Router v6** - Client-side routing

### UI & Styling
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Pre-built accessible components
- **Lucide React** - Icon library
- **Orbitron Font** - Google Fonts (cyberpunk aesthetic)

### Data Fetching & State
- **Axios** - HTTP client for API calls
- **TanStack Query (React Query)** - Server state management
- **React Hook Form** - Form handling
- **Zod** - Schema validation

---

## Project Structure

```
src/
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   ├── button.tsx
│   │   ├── card.tsx
│   │   ├── toast.tsx
│   │   └── ...
│   ├── Header.tsx             # App header with branding
│   └── FileUpload.tsx         # Drag-and-drop upload component
│
├── pages/
│   ├── Upload.tsx             # Video upload page (/)
│   ├── Processing.tsx         # Status monitoring page (/processing/:jobId)
│   ├── Results.tsx            # Results display page (/results/:jobId)
│   └── NotFound.tsx           # 404 page
│
├── lib/
│   ├── api.ts                 # API client and type definitions
│   └── utils.ts               # Utility functions (cn, etc.)
│
├── hooks/
│   └── use-toast.ts           # Toast notification hook
│
├── App.tsx                    # Main app component with routing
├── main.tsx                   # App entry point
└── index.css                  # Global styles and design tokens
```

---

## Setup & Installation

### Prerequisites
- Node.js 18+ and npm
- Backend API running on `http://localhost:5000`

### Installation Steps

```bash
# Clone the repository
git clone <repository-url>
cd truesight-frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Environment Variables
Currently, the API base URL is hardcoded in `src/lib/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:5000';
```

For production, update this to your deployed backend URL or use environment variables:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
```

---

## Design System

### Color Palette

#### Primary Colors (defined in `index.css`)
```css
--background: 222 47% 6%;        /* #0f0f0f - Dark background */
--foreground: 0 0% 95%;          /* Light text */
--primary: 15 100% 50%;          /* #ff3d00 - Cyberpunk red */
--primary-foreground: 0 0% 100%; /* White text on primary */
--secondary: 0 100% 40%;         /* Darker red variant */
--accent: 142 76% 50%;           /* #00ff41 - Green for REAL */
--destructive: 0 62.8% 30.6%;    /* Error red */
```

#### Semantic Usage
- **Primary Red (#ff3d00)**: Brand color, accents, FAKE verdict
- **Green (#00ff41)**: REAL verdict, success states
- **Dark Background (#0f0f0f)**: Main background
- **Card/Surface**: Slightly lighter than background with transparency

### Typography
- **Font Family**: Orbitron (from Google Fonts)
- **Font Weights**: 400 (regular), 700 (bold), 900 (black)
- **Usage**: Applied globally, tech/cyber aesthetic

### Custom Animations
```css
/* Pulsing glow effect for FAKE verdict */
@keyframes pulse-glow {
  0%, 100% { box-shadow: 0 0 20px rgba(255, 61, 0, 0.5); }
  50% { box-shadow: 0 0 40px rgba(255, 61, 0, 0.8); }
}

/* Pulsing glow effect for REAL verdict */
@keyframes pulse-glow-green {
  0%, 100% { box-shadow: 0 0 20px rgba(0, 255, 65, 0.5); }
  50% { box-shadow: 0 0 40px rgba(0, 255, 65, 0.8); }
}

/* Slow spinning loader */
@keyframes spin-slow {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}
```

### Responsive Breakpoints
Following Tailwind's default breakpoints:
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

---

## API Integration

### Base Configuration (`src/lib/api.ts`)

```typescript
const API_BASE_URL = 'http://localhost:5000';
```

### Endpoints

#### 1. Upload Video
```typescript
POST /upload

Request: FormData with 'video' field
Response: {
  job_id: string;
  message: string;
  status: string;
}
```

#### 2. Get Status
```typescript
GET /status/:jobId

Response: {
  job_id: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  message: string;
  error?: string;
}
```

**Note**: Backend does NOT send progress percentage.

#### 3. Get Results
```typescript
GET /results/:jobId

Response: {
  job_id: string;
  status: string;
  verdict: 'FAKE' | 'REAL';
  confidence: number;
  probabilities: {
    fake_probability: number;
    real_probability: number;
  };
  analysis_time: string; // String with 's' suffix (e.g., "45.30s")
  model_predictions: {
    [modelKey: string]: {
      fake: number;
      real: number;
    };
  };
  gradcam_images: {
    average_heatmap: string;
    frame_overlays: string[];
  };
  metadata: {
    filename: string;
    filesize: string;
    upload_time: string;
    frames_analyzed: number;
  };
}
```

**Important Notes**:
- `probabilities` is a nested object containing `fake_probability` and `real_probability`
- `model_predictions` is an object (not array) with model keys as properties
- `gradcam_images` (not `gradcam_files`) contains image filenames
- `analysis_time` is a string with 's' suffix

#### 4. Get Grad-CAM Image
```typescript
GET /gradcam/:jobId/:filename

Returns: Image file (PNG/JPG)
```

### API Client Methods

```typescript
// Upload video file
api.uploadVideo(file: File): Promise<UploadResponse>

// Poll job status
api.getStatus(jobId: string): Promise<StatusResponse>

// Get final results
api.getResults(jobId: string): Promise<ResultsResponse>

// Generate Grad-CAM image URL
api.getGradCamUrl(jobId: string, filename: string): string
```

### Model Name Mapping

```typescript
export const MODEL_NAME_MAP: { [key: string]: string } = {
  efficientnet: 'EfficientNet-B4',
  inceptionv3: 'InceptionV3',
  resnet50: 'ResNet-50',
  xception: 'Xception',
};
```

---

## Components

### Header (`src/components/Header.tsx`)

**Purpose**: Application header with branding and tagline

**Features**:
- Search icon (visual branding)
- TrueSight title
- Subtitle: "Advanced AI-Powered Deepfake Detection & Forensic Analysis"
- Responsive text sizing
- Semi-transparent backdrop blur effect

**Usage**:
```tsx
import { Header } from "@/components/Header";

<Header />
```

---

### FileUpload (`src/components/FileUpload.tsx`)

**Purpose**: Drag-and-drop video upload interface

**Props**:
```typescript
interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isUploading: boolean;
}
```

**Features**:
- Drag-and-drop zone
- Click to browse file picker
- File validation:
  - Accepted formats: `.mp4`, `.avi`, `.mov`
  - Max size: 500MB
- Visual feedback for drag state
- Upload progress indication
- Error handling with toast notifications

**File Validation**:
```typescript
const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
const ACCEPTED_VIDEO_TYPES = [
  'video/mp4',
  'video/x-msvideo',
  'video/quicktime'
];
```

**Upload Button Text**: "Initiate Analysis" (uppercase, bold)

**Usage**:
```tsx
import { FileUpload } from "@/components/FileUpload";

<FileUpload 
  onFileSelect={handleFileSelect}
  isUploading={isUploading}
/>
```

---

## Pages

### Upload Page (`src/pages/Upload.tsx`)

**Route**: `/`

**Purpose**: Main landing page for video uploads

**Flow**:
1. User selects/drops video file
2. File validation occurs
3. Upload to backend via `api.uploadVideo()`
4. On success: Navigate to `/processing/:jobId`
5. On error: Display error toast

**State**:
```typescript
const [isUploading, setIsUploading] = useState(false);
```

**Key Functions**:
```typescript
const handleFileSelect = async (file: File) => {
  setIsUploading(true);
  try {
    const response = await api.uploadVideo(file);
    toast({ title: "Upload successful" });
    navigate(`/processing/${response.job_id}`);
  } catch (error) {
    toast({ title: "Upload failed", variant: "destructive" });
    setIsUploading(false);
  }
};
```

---

### Processing Page (`src/pages/Processing.tsx`)

**Route**: `/processing/:jobId`

**Purpose**: Monitor analysis progress with polling

**Polling Configuration**:
- Interval: 2 seconds
- Immediate first poll on mount
- Auto-cleanup on unmount
- No progress bar (backend doesn't send progress data)

**Status Flow**:
```
queued → processing → completed (navigate to results)
                    → failed (show error toast)
```

**State**:
```typescript
const [status, setStatus] = useState<StatusResponse | null>(null);
```

**Polling Logic**:
```typescript
useEffect(() => {
  const pollStatus = async () => {
    const response = await api.getStatus(jobId);
    setStatus(response);
    
    if (response.status === "completed") {
      navigate(`/results/${jobId}`);
    } else if (response.status === "failed") {
      toast({ title: "Analysis failed", variant: "destructive" });
    }
  };

  pollStatus();
  const interval = setInterval(pollStatus, 2000);
  
  return () => clearInterval(interval);
}, [jobId]);
```

**UI Elements**:
- Spinning loader icon with glow effect
- Status message (e.g., "Processing video frames...")
- Job ID display
- No progress bar (backend doesn't provide progress data)

---

### Results Page (`src/pages/Results.tsx`)

**Route**: `/results/:jobId`

**Purpose**: Display comprehensive analysis results

**Data Fetching**:
```typescript
useEffect(() => {
  const fetchResults = async () => {
    setLoading(true);
    const data = await api.getResults(jobId);
    setResults(data);
    setLoading(false);
  };
  fetchResults();
}, [jobId]);
```

**UI Sections**:

#### 1. Verdict Banner
- **FAKE**: Red background with pulsing glow animation
- **REAL**: Green background with pulsing glow animation
- Large prominent display with confidence percentage

#### 2. Analysis Summary Cards
Four metric cards displaying:
- **Confidence**: Overall confidence level
- **Fake Probability**: Likelihood of being fake
- **Real Probability**: Likelihood of being real
- **Analysis Time**: Processing duration

#### 3. Model Predictions Table
Tabular view of individual model outputs:
| Model Name | Fake % | Real % |
|------------|--------|--------|
| EfficientNet-B4 | 92% | 8% |
| InceptionV3 | 85% | 15% |
| ResNet-50 | 84% | 16% |
| Xception | 88% | 12% |

**Note**: Model predictions are returned as an object, not an array. Use `Object.entries()` to iterate:
```typescript
Object.entries(results.model_predictions).map(([modelKey, preds]) => (
  <tr key={modelKey}>
    <td>{MODEL_NAME_MAP[modelKey] || modelKey}</td>
    <td>{(preds.fake * 100).toFixed(1)}%</td>
    <td>{(preds.real * 100).toFixed(1)}%</td>
  </tr>
))
```

#### 4. Visual Explanations (Grad-CAM)
- **Average Heatmap**: Overall attention map
- **Frame Overlays**: Individual frame heatmaps in a responsive grid

#### 5. Metadata Section
- Original filename
- File size
- Upload timestamp
- Number of frames analyzed

**Loading State**:
- Skeleton loaders for all sections
- Smooth transition to actual content

**Error Handling**:
- Displays error toast on fetch failure
- Graceful degradation if data missing

---

## Critical Implementation Notes

### Data Access Patterns

**1. Accessing Probabilities (Nested Object)**
```typescript
// ❌ WRONG
const fakeProb = results.fake_probability;
const realProb = results.real_probability;

// ✅ CORRECT
const fakeProb = results.probabilities.fake_probability;
const realProb = results.probabilities.real_probability;
```

**2. Iterating Model Predictions (Object, Not Array)**
```typescript
// ❌ WRONG - it's not an array
results.model_predictions.map(model => ...)

// ✅ CORRECT - it's an object
Object.entries(results.model_predictions).map(([modelKey, preds]) => (
  <tr key={modelKey}>
    <td>{MODEL_NAME_MAP[modelKey] || modelKey}</td>
    <td>{(preds.fake * 100).toFixed(1)}%</td>
    <td>{(preds.real * 100).toFixed(1)}%</td>
  </tr>
))
```

**3. Grad-CAM Image URLs**
```typescript
// ❌ WRONG - incorrect field name
<img src={results.gradcam_files.average_heatmap} />

// ✅ CORRECT - use gradcam_images and construct full URL
<img src={api.getGradCamUrl(jobId, results.gradcam_images.average_heatmap)} />
```

**4. Analysis Time (String with Suffix)**
```typescript
// ❌ WRONG - it's not a number
<p>{results.analysis_time.toFixed(2)}s</p>

// ✅ CORRECT - it's already a string with 's' suffix
<p>{results.analysis_time}</p>
```

**5. Status Polling (No Progress)**
```typescript
// ❌ WRONG - backend doesn't send progress
{status.progress && <ProgressBar value={status.progress} />}

// ✅ CORRECT - use indeterminate spinner
<Loader2 className="animate-spin" />
```

---

## Routing

### Route Configuration (`src/App.tsx`)

```tsx
<BrowserRouter>
  <Routes>
    <Route path="/" element={<Upload />} />
    <Route path="/processing/:jobId" element={<Processing />} />
    <Route path="/results/:jobId" element={<Results />} />
    <Route path="*" element={<NotFound />} />
  </Routes>
</BrowserRouter>
```

### Navigation Flow

```
User Journey:
┌─────────────┐
│   Upload    │  User uploads video
│     (/)     │
└──────┬──────┘
       │ Upload successful
       │ (GET job_id)
       ▼
┌─────────────┐
│ Processing  │  Poll status every 2s
│ (:jobId)    │
└──────┬──────┘
       │ Status = 'completed'
       ▼
┌─────────────┐
│  Results    │  Display final analysis
│ (:jobId)    │
└─────────────┘
```

### Route Parameters
- `:jobId` - Unique identifier for the analysis job
  - Example: `/processing/abc-123-def-456`
  - Used to fetch status and results from backend

---

## Features

### 1. File Upload
- **Drag-and-Drop**: Native HTML5 drag-and-drop API
- **File Browser**: Traditional file input fallback
- **Validation**: Format and size checks before upload
- **Progress Feedback**: Visual indicators during upload

### 2. Real-Time Status Monitoring
- **Polling**: Automatic status checks every 2 seconds
- **Progress Bar**: Visual representation of analysis progress
- **Auto-Navigation**: Redirects to results when complete
- **Error Handling**: Alerts user if processing fails

### 3. Results Visualization
- **Verdict Display**: Large, color-coded verdict banner
- **Metrics Dashboard**: Key statistics in card format
- **Model Breakdown**: Detailed predictions from each model
- **Visual Explanations**: Grad-CAM heatmaps for interpretability
- **Metadata**: Comprehensive file and analysis information

### 4. Responsive Design
- **Mobile First**: Optimized for small screens
- **Breakpoint Adaptations**:
  - Mobile: Single column layout
  - Tablet: Two-column grids
  - Desktop: Multi-column layouts with larger text
- **Touch-Friendly**: Large tap targets, appropriate spacing

### 5. Error Handling
- **Upload Errors**: Toast notifications with error details
- **Network Errors**: Axios error handling with retry capability
- **404 Handling**: Custom NotFound page
- **Validation Errors**: Inline feedback for invalid files

### 6. Accessibility
- **ARIA Labels**: Semantic HTML and ARIA attributes
- **Keyboard Navigation**: Full keyboard support
- **Screen Readers**: Descriptive text for assistive technologies
- **Color Contrast**: WCAG AA compliant (except decorative elements)

---

## Error Handling

### Client-Side Validation
```typescript
// File size validation
if (file.size > MAX_FILE_SIZE) {
  toast({
    title: "File too large",
    description: "Maximum file size is 500MB",
    variant: "destructive"
  });
  return;
}

// File type validation
if (!ACCEPTED_VIDEO_TYPES.includes(file.type)) {
  toast({
    title: "Invalid file type",
    description: "Please upload MP4, AVI, or MOV files",
    variant: "destructive"
  });
  return;
}
```

### API Error Handling
```typescript
try {
  const response = await api.uploadVideo(file);
  // Success handling
} catch (error: any) {
  toast({
    title: "Upload failed",
    description: error.response?.data?.error || "Please try again",
    variant: "destructive"
  });
}
```

### Network Errors
- Axios automatically handles network timeouts
- Error responses are caught and displayed via toast
- User can retry failed operations

### Status Polling Errors
- Non-blocking: Continues polling even if one request fails
- Error toast displayed but polling continues
- Manual retry available via page refresh

---

## Deployment

### Build Process
```bash
# Production build
npm run build

# Output directory: dist/
```

### Static Hosting Options
- **Vercel**: Zero-config deployment
- **Netlify**: Continuous deployment from Git
- **AWS S3 + CloudFront**: Scalable static hosting
- **GitHub Pages**: Free hosting for public repos

### Environment Configuration

Create `.env.production`:
```env
VITE_API_BASE_URL=https://api.truesight.example.com
```

Update `src/lib/api.ts`:
```typescript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';
```

### Backend Requirements
- CORS must be enabled for frontend domain
- All API endpoints must be accessible from production URL
- Grad-CAM images must be served with appropriate CORS headers

### Deployment Checklist
- [ ] Update API base URL for production
- [ ] Enable CORS on backend for production domain
- [ ] Test all routes and API integrations
- [ ] Verify Grad-CAM images load correctly
- [ ] Test responsive design on multiple devices
- [ ] Check browser console for errors
- [ ] Optimize images and assets
- [ ] Configure CDN (optional)
- [ ] Set up monitoring and analytics (optional)

---

## Development Guidelines

### Code Style
- **TypeScript**: Strict mode enabled
- **ESLint**: Enforced linting rules
- **Prettier**: Auto-formatting on save
- **Naming**: camelCase for variables, PascalCase for components

### Component Structure
```tsx
// 1. Imports
import { useState } from "react";
import { Button } from "@/components/ui/button";

// 2. Types/Interfaces
interface MyComponentProps {
  title: string;
}

// 3. Component
export const MyComponent = ({ title }: MyComponentProps) => {
  // 3a. Hooks
  const [state, setState] = useState();
  
  // 3b. Event handlers
  const handleClick = () => {};
  
  // 3c. Render
  return <div>{title}</div>;
};
```

### Adding New Features
1. Create component in appropriate directory
2. Add types/interfaces in the same file or `src/types/`
3. Update routing if needed
4. Add error handling
5. Test responsive design
6. Document in this file

---

## Troubleshooting

### Common Issues

**Issue**: CORS errors when calling API
- **Solution**: Ensure backend has CORS enabled for frontend domain

**Issue**: Grad-CAM images not loading
- **Solution**: Check backend URL, verify images are served with correct headers

**Issue**: Upload fails silently
- **Solution**: Check browser console, verify file size/format, check network tab

**Issue**: Polling doesn't stop
- **Solution**: Verify cleanup function in useEffect, check jobId validity

**Issue**: Styles not applying
- **Solution**: Run `npm run dev` to rebuild, check Tailwind config, verify CSS imports

---

## Future Enhancements

### Planned Features
- [ ] Batch upload support
- [ ] Download results as PDF report
- [ ] Historical analysis dashboard
- [ ] User authentication and saved analyses
- [ ] Real-time WebSocket updates (replace polling)
- [ ] Video preview before upload
- [ ] Detailed model performance metrics
- [ ] Confidence threshold customization
- [ ] Multi-language support

### Performance Optimizations
- [ ] Implement React Query for better caching
- [ ] Add service worker for offline support
- [ ] Lazy load Grad-CAM images
- [ ] Code splitting for faster initial load
- [ ] Image optimization and compression

---

## Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make changes and test thoroughly
4. Commit with descriptive messages: `git commit -m "Add feature X"`
5. Push to your fork: `git push origin feature/my-feature`
6. Create a pull request

### Pull Request Guidelines
- Include description of changes
- Reference related issues
- Add screenshots for UI changes
- Ensure all tests pass
- Update documentation if needed

---

## License

[Specify your license here]

---

## Contact & Support

- **Documentation**: This file
- **Issues**: [GitHub Issues](your-repo-url/issues)
- **Email**: support@truesight.example.com

---

**Last Updated**: 2025-01-16
**Version**: 1.0.0
