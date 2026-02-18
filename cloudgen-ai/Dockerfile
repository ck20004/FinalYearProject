### STAGE 1: Build the React application ###
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json ./
RUN npm install

# Copy the rest of the application source code
COPY . .

# Set the API base URL for the containerized backend
# The backend will be available at http://backend:8000 within the Docker network
# We will configure Nginx to proxy requests from /api to the backend
ARG VITE_AGENT_API_BASE=
ENV VITE_AGENT_API_BASE=${VITE_AGENT_API_BASE}

# Build the static files
RUN npm run build

### STAGE 2: Serve the static files with Nginx ###
FROM nginx:1.25-alpine

# Copy the built static files from the builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom Nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for the web server
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]