module.exports = {
  apps: [
    {
      name: 'info-butler-backend',
      cwd: './',
      script: 'uv',
      args: 'run uvicorn backend.main:app --host 0.0.0.0 --port 8001',
      interpreter: 'none',
      watch: false,
      autorestart: true,
      max_restarts: 3,
      env: {
        NODE_ENV: 'development'
      }
    },
    {
      name: 'info-butler-frontend',
      cwd: './frontend',
      script: 'npm',
      args: 'run dev',
      watch: false,
      autorestart: true,
      max_restarts: 3
    }
  ]
};
