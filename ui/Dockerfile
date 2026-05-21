FROM node:22-slim AS builder

WORKDIR /app

# Copy dependency files
COPY package.json ./

# Install dependencies (avoid lockfile to keep it platform-agnostic)
RUN npm install --no-package-lock

# Copy the rest of the application
COPY . .

# Build the Vite application
RUN npm run build

FROM nginx:alpine

# Copy the build output
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy the custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
