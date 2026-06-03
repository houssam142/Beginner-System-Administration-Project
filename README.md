# My-First-System-Design-Project


# Backend infrastructure lab

## 1. Goal
this is a a simple infrastructure, consists of three virtual machines, each has a separate responsibility:
VM1 runs NGINX and acts as the public entry point of the infrastructure, it receives client requests over HTTP/HTTPS,
redirects HTTP traffic to HTTPS, terminates TLS using a self-signed certificate, and forwards requests to the backend
application on VM2.
# VM2: Backend Application Server
VM2 runs a Flask backend application managed by systemd.
The application exposes several endpoints, including "/", "/health", "/headers",
"/db-health" and "/visits". It handles incoming requests from NGINX and connects to
the database when needed.
# VM3: Database Server
VM3 runs a database server (MariaDB). It stores the application data and only accepts
database connections from VM2. The database is not directly exposed to VM1 or the host machine.
