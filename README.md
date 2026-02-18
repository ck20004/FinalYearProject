# CloudGen.AI

## Project Overview
CloudGen.AI is a full-stack web app for automated AWS cloud architecture generation and optimization using AI.

## Prerequisites
- Node.js (v18+ recommended)
- npm (comes with Node.js)
- MongoDB Atlas account (or local MongoDB)
- Git

## Getting Started

### 1. Clone the repository
```sh
git clone https://github.com/<your-org-or-username>/<your-repo-name>.git
cd cloudgen-ai
```

### 2. Install frontend dependencies
```sh
npm install
```

### 3. Install backend dependencies
```sh
cd backend
npm install
```

### 4. Set up environment variables
- Copy `.env` from `backend/.env.example` (if available) or edit `backend/.env` with your MongoDB URI and JWT secret.

### 5. Start the backend server
```sh
npm start
```
- The backend runs on [http://localhost:5000](http://localhost:5000)

### 6. Start the frontend (React) app
```sh
cd ..
npm run dev
```
- The frontend runs on [http://localhost:5173](http://localhost:5173)

## Usage
- Open [http://localhost:5173](http://localhost:5173) in your browser.
- Sign up, log in, and use the dashboard features.

## Troubleshooting
- If you get MongoDB errors, check your `.env` file and MongoDB connection.
- For port issues, change `PORT` in `backend/.env`.

## Folder Structure
- `src/` - React frontend code
- `backend/` - Node.js/Express backend API
- `public/` - Static assets

## Contact
For help, contact the project owner or open an issue on GitHub.
