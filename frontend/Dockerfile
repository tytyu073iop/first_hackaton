FROM node:25

WORKDIR /app

# Install 'serve' globally
RUN npm install -g serve

# Copy package files and install dependencies
COPY frontend/package*.json ./
RUN npm install

# Copy the rest of the frontend source code
COPY frontend/ .

# Expose the port
EXPOSE 5173

# Build the app AND serve it at runtime
# We use 'sh -c' to run multiple commands in the CMD
CMD ["sh", "-c", "npm run build && serve -s dist -l 5173"]