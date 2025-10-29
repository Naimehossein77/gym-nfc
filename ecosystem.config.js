module.exports = {
  apps: [{
    name: 'gym-nfc',
    script: 'main.py',
    interpreter: '/root/gym-nfc-env//bin/python',
    cwd: '/root/gym-nfc',

    // Environment variables
    env: {
      PYTHONPATH: '/root/gym-nfc',
      HOST: '0.0.0.0',
      PORT: '8001',
      DEBUG: 'False'
    },

    // Process management
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '16G',

    // Logging
    error_file: '/root/gym-nfc/logs/err.log',
    out_file: '/root/gym-nfc/logs/out.log',
    log_file: '/root/gym-nfc/logs/combined.log',
    time: true,

    // Restart policy
    restart_delay: 10000,
    max_restarts: 100,
    min_uptime: '10s'
  }]
};
