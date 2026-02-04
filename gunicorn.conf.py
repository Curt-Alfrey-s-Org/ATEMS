# Gunicorn config — ensures bind 0.0.0.0 for Traefik/Docker reachability
bind = "0.0.0.0:5000"
workers = 2
timeout = 120
