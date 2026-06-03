#!/bin/bash

chown -R mysql:mysql /var/lib/mysql
chmod -R 755 /var/lib/mysql

if [ -d /var/lib/mysql ]; then
	mariadb-install-db --user=mysql
fi

mysqld --user=mysql &

mysql -u root <<EOF
CREATE DATABASE IF NOT EXISTS backend_data;
CREATE USER 'backend_user'@'192.168.56.10' IDENTIFIED BY '1234';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE on backend_data.* TO 'backend_user'@'192.168.56.10';
FLUSH PRIVILEGES;

USE backend_data;

CREATE TABLE IF NOT EXISTS visits (
    id INT AUTO_INCREMENT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    client_ip VARCHAR(255),
    user_agent TEXT
);

EOF

mysqladmin shutdown

mysqld --user=mysql
