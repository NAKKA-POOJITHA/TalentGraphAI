FROM node:18-alpine

WORKDIR /workspace

# Copy dependency configs
COPY package*.json ./

# Install packages
RUN npm install

# Copy application files
COPY . .

# Expose Vite dev server port
EXPOSE 5173

# Run Vite dev server in host mode
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
