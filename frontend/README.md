# AI HR Interviewer Frontend

A premium, AI-driven recruitment platform built with React, Vite, Tailwind CSS, and Framer Motion. This frontend is designed to work with a microservices backend architecture distributed across ports 8001, 8002, and 8003.

## Features
- **Modern Glassmorphism UI**: High-end look with smooth animations.
- **Service Orchestration**: Custom API client handling communication with three backend ports.
- **Authentication**: Secure Login/Register flow with protected routing.
- **Resume Analysis Workspace**: Drag-and-drop resume upload for analysis.
- **Interview Room**: Immersive interface with camera access and real-time AI questions.

## Prerequisites
- Node.js (v16.0.0 or higher)
- npm or yarn
- Backend microservices running on:
    - `http://localhost:8001` (Auth Service)
    - `http://localhost:8002` (Resume/Analysis Service)
    - `http://localhost:8003` (Interview Service)

## Installation

1. Install dependencies:
    npm install

2. Start the development server:
    npm run dev

3. Build for production:
    npm run build

## Project Structure
- `src/services/api.js`: Handles logic for multi-port backend connectivity.
- `src/context/AuthContext.jsx`: Manages global user state and token persistence.
- `src/pages/Dashboard.jsx`: The primary landing zone for authenticated users to upload resumes.
- `src/pages/InterviewRoom.jsx`: The real-time AI interview environment.

## Troubleshooting
- **CORS Errors**: Ensure your backend services have CORS enabled for `http://localhost:3000`.
- **Media Access**: The interview room requires Camera and Microphone permissions. Use `https` for production or `localhost` for dev to access these APIs.
- **Port Conflicts**: This app runs on port 3000 by default. If it's taken, update `vite.config.js`.
