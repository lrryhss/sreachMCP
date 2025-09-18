# Use Node.js Alpine image for smaller size
FROM node:20-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy all source files
COPY . .

# Expose the default Next.js port
EXPOSE 3000

# Set environment to development for hot-reload
ENV NODE_ENV=development

# Run the development server
CMD ["npm", "run", "dev"]