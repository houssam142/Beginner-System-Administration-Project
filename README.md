# My-First-System-Design-Project


# Backend infrastructure lab

## 1. Goal
this is a a simple infrastructure, consists of three virtual machines, each has a separate responsibility:
  # VM1: Reverse Proxy Server
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
The purpose of this lab is to practice basic system administration concepts such as virtual
machine networking, reverse proxying, HTTP configuration, firewall rules, service management with
systemd, database connectivity, logging, and failure testing.

# Architecture
The infrastructure is composed of three virtual machines connected through a private network (host-only adapter).
```
Host Machine
     |
     | HTTPS :443
     v
VM1 - NGINX Reverse Proxy
     |
     | HTTP :8080
     v
VM2 - Flask Backend
     |
     | MariaDB :3306
     v
VM3 - MariaDB Database
```
# Network Table
```
| Machine | Role | IP Address | Main Service | Open Ports |
|---|---|---:|---|---|
| VM1 | Reverse proxy | `192.168.56.20` | NGINX | 22, 80, 443 |
| VM2 | Backend app | `182.168.56.10` | Flask backend | 22, 8080 from VM1 only |
| VM3 | Database | `192.168.56.30` | MariaDB | 22, 3306 from VM2 only |
```

## Request Flow

When a client sends a request to the infrastructure, the request first reaches NGINX on VM1.

NGINX listens on port 443 for HTTPS traffic. It terminates TLS using a self-signed certificate, then forwards the request to the Flask backend running on VM2 at port 8080.

The Flask application handles the request based on the URI:

- `/` returns a basic backend response.
- `/health` checks if the Flask application is alive.
- `/headers` returns the headers received from NGINX.
- `/db-health` checks if Flask can connect to MariaDB.
- `/visits` writes a visit record to MariaDB and returns the total number of visits.

If the request needs database access, VM2 connects to MariaDB on VM3 using port 3306. MariaDB only accepts database connections from VM2.
