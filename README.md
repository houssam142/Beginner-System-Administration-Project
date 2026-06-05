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

If the request needs database access, VM2 connects to MariaDB on VM3 using port 3306. MariaDB only accepts database connections from VM2, using Uncomplicated firewall (ufw) rule ```ufw allow in from <VM2_IP_ADDRESS> to <VM3_IP_ADDRESS> port 3306 proto tcp```.
Firewall Rules

Firewall rules are used to restrict access between the machines.

Expected access:

Source	Destination	Port	Purpose
Client / Host	VM1	80	Redirect HTTP to HTTPS
Client / Host	VM1	443	Access the application through HTTPS
VM1	VM2	8080	Forward requests to Flask
VM2	VM3	3306	Connect to MariaDB

Blocked access:

Source	Destination	Reason
Client / Host	VM2:8080	Backend should not be accessed directly
Client / Host	VM3:3306	Database should not be public
VM1	VM3:3306	Reverse proxy does not need database access

Example firewall rule for VM3:

sudo ufw allow from <VM2_IP> to any port 3306 proto tcp

This allows MariaDB access only from VM2.

5. Services and Configuration

Each virtual machine runs a specific service. The services are managed by systemd so they can be started, stopped, restarted, inspected, and enabled at boot.

VM1: NGINX Reverse Proxy

VM1 runs NGINX.

NGINX is responsible for receiving client requests, redirecting HTTP traffic to HTTPS, terminating TLS, and forwarding requests to the Flask backend on VM2.

Important configuration files:

/etc/nginx/nginx.conf
/etc/nginx/sites-available/<site_config>
/etc/nginx/sites-enabled/<site_config>
/etc/ssl/certs/<certificate_file>
/etc/ssl/private/<private_key_file>

Useful commands:

sudo nginx -t
sudo systemctl status nginx
sudo systemctl restart nginx
sudo systemctl reload nginx
sudo journalctl -u nginx --no-pager

Important logs:

/var/log/nginx/access.log
/var/log/nginx/error.log

NGINX forwards requests to the backend application using the backend server IP and port:

http://<VM2_IP>:8080

The reverse proxy also forwards headers to the backend:

proxy_set_header Host $host;
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;

These headers allow the backend to know the original host, client IP, proxy chain, and protocol used by the client.

VM2: Flask Backend Application

VM2 runs the Flask backend application.

The backend listens on port 8080 and receives requests from NGINX on VM1.

Application endpoints:

/           Basic response from the backend
/health     Checks if the Flask app is running
/headers    Shows headers received from NGINX
/db-health  Checks if Flask can connect to MariaDB
/visits     Inserts a visit into MariaDB and returns the visit count

Important files:

/opt/backend-lab/app.py
/opt/backend-lab/venv/
/etc/backend-lab/backend.env
/etc/systemd/system/backend.service

Useful commands:

sudo systemctl status backend
sudo systemctl start backend
sudo systemctl stop backend
sudo systemctl restart backend
sudo systemctl enable backend
sudo journalctl -u backend -f

The backend service reads database configuration from:

/etc/backend-lab/backend.env

Example environment file:

DB_HOST=192.168.1.30
DB_PORT=3306
DB_NAME=backend_data
DB_USER=backend_user
DB_PASSWORD=<database_password>

The environment file should not be world-readable because it contains database credentials.

Recommended permissions:

sudo chown root:root /etc/backend-lab/backend.env
sudo chmod 600 /etc/backend-lab/backend.env

The backend should be managed by systemd, not started manually with python app.py.

VM3: MariaDB Database Server

VM3 runs MariaDB.

MariaDB stores application data for the Flask backend. It listens on port 3306 and should only accept database connections from VM2.

Important configuration file:

/etc/mysql/mariadb.conf.d/50-server.cnf

Important database objects:

Database: backend_data
User: backend_user
Table: visits

Useful commands:

sudo systemctl status mariadb
sudo systemctl start mariadb
sudo systemctl stop mariadb
sudo systemctl restart mariadb
sudo systemctl enable mariadb
sudo journalctl -u mariadb -f
sudo mysql

Check if MariaDB is listening:

sudo ss -ltnp | grep 3306

MariaDB should listen on the expected VM3 IP or on all interfaces if firewall rules are strict:

192.168.1.30:3306

or:

0.0.0.0:3306

For stricter configuration, MariaDB can be bound directly to VM3’s service IP:

[mysqld]
bind-address = 192.168.1.30
skip-name-resolve

The MariaDB user should be allowed from VM2’s IP address, not from everywhere.

Example:

CREATE USER 'backend_user'@'<VM2_IP>' IDENTIFIED BY '<database_password>';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE
ON backend_data.*
TO 'backend_user'@'<VM2_IP>';

FLUSH PRIVILEGES;

The % wildcard should not be used for this project because the database user should not be allowed to connect from any machine.

6. Backend Application Behavior

The Flask backend exposes these endpoints:

/

Returns a basic response from the backend.

Example:

curl -k https://<VM1_IP>/

Expected result:

Hello from backend VM
/health

Checks whether the Flask application itself is alive.

Example:

curl -k https://<VM1_IP>/health

Expected result:

OK

This endpoint does not check the database. It only verifies that the backend application is running.

/headers

Shows the headers received by the Flask backend.

Example:

curl -k https://<VM1_IP>/headers

This endpoint is useful for verifying that NGINX forwards headers such as:

Host
X-Real-IP
X-Forwarded-For
X-Forwarded-Proto
/db-health

Checks whether the Flask backend can connect to MariaDB.

Example:

curl -k https://<VM1_IP>/db-health

Expected result:

DB OK

If MariaDB is stopped, unreachable, or the credentials are wrong, this endpoint should return:

DB ERROR
/visits

Inserts a visit record into the MariaDB database and returns the total number of visits.

Example:

curl -k https://<VM1_IP>/visits

Expected result:

Visit recorded.
Total visits: <number>

This endpoint proves that the backend can both write to and read from the database.

7. Testing
Happy Path Tests

From the host machine:

curl -k -I http://<VM1_IP>/
curl -k -I https://<VM1_IP>/
curl -k https://<VM1_IP>/
curl -k https://<VM1_IP>/health
curl -k https://<VM1_IP>/headers
curl -k https://<VM1_IP>/db-health
curl -k https://<VM1_IP>/visits

Expected results:

HTTP redirects to HTTPS.
/ returns the backend response.
/health returns OK.
/headers returns headers received from NGINX.
/db-health returns DB OK.
/visits inserts a visit and returns the total count.
Backend Isolation Test

From the host machine:

curl http://<VM2_IP>:8080/

Expected result:

This should fail if the firewall blocks direct backend access from the host.

From VM1:

curl http://<VM2_IP>:8080/

Expected result:

This should work because VM1 is allowed to reach VM2.
Database Isolation Test

From VM2:

mysql -h 192.168.1.30 -u backend_user -p backend_data

Expected result:

Connection should succeed.

From VM1:

mysql -h 192.168.1.30 -u backend_user -p backend_data

Expected result:

Connection should fail.

From the host machine:

mysql -h 192.168.1.30 -u backend_user -p backend_data

Expected result:

Connection should fail.
8. Failure Tests

Failure testing is used to verify that the infrastructure behaves predictably when one layer breaks.

Test 1: Stop MariaDB

On VM3:

sudo systemctl stop mariadb

From the host:

curl -k https://<VM1_IP>/health
curl -k https://<VM1_IP>/db-health
curl -k https://<VM1_IP>/visits

Expected result:

/health returns OK.
/db-health returns DB ERROR.
/visits returns DB ERROR.

Explanation:

The Flask application is still alive, but it cannot connect to MariaDB. This proves that application health and database health are separate checks.

Logs to check on VM2:

sudo journalctl -u backend --no-pager | tail -n 80

Fix:

sudo systemctl start mariadb
Test 2: Stop Backend Service

On VM2:

sudo systemctl stop backend

From the host:

curl -k -I https://<VM1_IP>/

Expected result:

502 Bad Gateway

Explanation:

NGINX is still running on VM1, but it cannot reach the Flask backend on VM2.

Logs to check on VM1:

sudo tail -n 50 /var/log/nginx/error.log

Fix:

sudo systemctl start backend
Test 3: Block VM2 from Reaching MariaDB

On VM3, temporarily block VM2 from accessing port 3306.

Example with UFW:

sudo ufw deny from <VM2_IP> to any port 3306 proto tcp
sudo ufw reload

From the host:

curl -k https://<VM1_IP>/db-health

Expected result:

DB ERROR

Explanation:

The backend is alive, but the firewall prevents it from reaching MariaDB.

Logs to check on VM2:

sudo journalctl -u backend --no-pager | tail -n 80

Fix:

sudo ufw delete deny from <VM2_IP> to any port 3306 proto tcp
sudo ufw allow from <VM2_IP> to any port 3306 proto tcp
sudo ufw reload
Test 4: Wrong Database Password

On VM2, edit:

/etc/backend-lab/backend.env

Set an incorrect database password:

DB_PASSWORD=wrong_password

Restart the backend:

sudo systemctl restart backend

Expected result:

The backend should fail to connect to the database, or /db-health should return DB ERROR.

Logs to check:

sudo journalctl -u backend -f

Fix:

Restore the correct database password in /etc/backend-lab/backend.env.

Then restart:

sudo systemctl restart backend
Test 5: Reboot Persistence

Reboot VM1, VM2, and VM3.

After reboot, without manually starting services, run from the host:

curl -k https://<VM1_IP>/health
curl -k https://<VM1_IP>/db-health
curl -k https://<VM1_IP>/visits

Expected result:

/health returns OK.
/db-health returns DB OK.
/visits records a visit and returns the total count.

Explanation:

This proves that NGINX, the Flask backend, and MariaDB are enabled at boot and start automatically.

Useful checks:

sudo systemctl is-enabled nginx
sudo systemctl is-enabled backend
sudo systemctl is-enabled mariadb
9. Logs and Debugging

Each layer has its own logs.

VM1: NGINX

Access log:

sudo tail -f /var/log/nginx/access.log

Error log:

sudo tail -f /var/log/nginx/error.log

Use NGINX logs when:

The client receives 502 Bad Gateway.
HTTPS fails.
NGINX cannot reach the backend.
The reverse proxy configuration is wrong.
VM2: Backend Application

Backend logs:

sudo journalctl -u backend -f

Backend status:

sudo systemctl status backend

Use backend logs when:

/db-health returns DB ERROR.
/visits returns DB ERROR.
The backend service crashes.
The database credentials are wrong.
VM3: MariaDB

MariaDB logs:

sudo journalctl -u mariadb -f

MariaDB status:

sudo systemctl status mariadb

Check listening ports:

sudo ss -ltnp | grep 3306

Use MariaDB logs when:

The backend cannot connect to the database.
MariaDB fails to start.
The database user or permissions are wrong.
10. Security Notes

This project is a lab, but basic security boundaries are still enforced.

Security decisions:

VM1 is the only public entry point.
VM2 should not be accessed directly by clients.
VM3 should only accept database connections from VM2.
The backend runs as a systemd service.
Database credentials are stored outside the application code.
The environment file should be readable only by root.
MariaDB should not allow backend_user from every host.

Important checks:

sudo ufw status verbose
sudo ss -tulnp
ls -l /etc/backend-lab/backend.env

Recommended environment file permissions:

sudo chmod 600 /etc/backend-lab/backend.env
sudo chown root:root /etc/backend-lab/backend.env
11. Backup and Restore

A database without backups is not reliable infrastructure.

Backup

On VM3:

sudo mkdir -p /var/backups/backend-lab
sudo mysqldump backend_data > /var/backups/backend-lab/backend_data_$(date +%Y-%m-%d_%H-%M-%S).sql

Check backups:

ls -lh /var/backups/backend-lab
Restore

To restore a backup:

sudo mysql backend_data < /var/backups/backend-lab/<backup_file>.sql

A backup should not be trusted until it has been restored successfully.

12. Rebuild Notes

To rebuild the infrastructure from scratch:

Create three virtual machines.
Configure networking and assign the correct IP addresses.
Install and configure NGINX on VM1.
Generate or install the self-signed TLS certificate on VM1.
Configure NGINX to proxy requests to VM2.
Install Python, Flask, and PyMySQL on VM2.
Create the backend application and backend.service.
Create /etc/backend-lab/backend.env on VM2.
Install and configure MariaDB on VM3.
Create the database, user, grants, and visits table.
Configure firewall rules on all VMs.
Enable all services at boot.
Run the happy path tests.
Run the failure tests.

Services that should be enabled at boot:

sudo systemctl enable nginx
sudo systemctl enable backend
sudo systemctl enable mariadb
13. Known Limitations

This project is a learning lab, not a production deployment.

Known limitations:

The TLS certificate is self-signed.
There is no real domain name.
The Flask development server is used instead of a production WSGI server.
There is no automated deployment system yet.
Backups are manual unless a cron job or systemd timer is added.
Monitoring is basic.
Secrets are stored in an environment file, not a dedicated secret manager.
