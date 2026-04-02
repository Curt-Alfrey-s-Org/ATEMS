# Changing MySQL Credentials (Alfa WordPress)

Use this guide when you want to change `MYSQL_DATABASE`, `MYSQL_USER`, `MYSQL_PASSWORD`, or `MYSQL_ROOT_PASSWORD` in `.env` without losing WordPress data.

**Important:** MySQL only applies `MYSQL_*` env vars on first run (empty data dir). For existing volumes, you must update MySQL manually to match your new `.env`.

---

## 1. Discover Current Credentials

```bash
docker exec alfa_wordpress_1 env | grep WORDPRESS_DB
```

---

## 2. Connect to MySQL

Replace `CHANGE_ME` with the actual password.

**As root:**
```bash
sudo docker exec -it alfa_db_1 mysql -u root -p'CHANGE_ME' -e "SELECT 1;"
```

**As app user:**
```bash
sudo docker exec -it alfa_db_1 mysql -u CHANGE_ME -p'CHANGE_ME' -e "SELECT 1;"
```

---

## 3. Update .env

Edit `~/alfa/.env`:

```
MYSQL_ROOT_PASSWORD=CHANGE_ME
MYSQL_DATABASE=CHANGE_ME
MYSQL_USER=CHANGE_ME
MYSQL_PASSWORD=CHANGE_ME
```

---

## 4. Apply Changes in MySQL

Replace placeholders:
- `OLD_ROOT_PW` = current root password
- `NEW_ROOT_PW` = new MYSQL_ROOT_PASSWORD
- `OLD_DB` = current database name (e.g. wordpress)
- `NEW_DB` = new MYSQL_DATABASE
- `OLD_USER` = current MySQL username
- `NEW_USER` = new MYSQL_USER
- `NEW_PW` = new MYSQL_PASSWORD

### 4a. Changing database name (NEW_DB ≠ OLD_DB)

```bash
sudo docker exec -it alfa_db_1 mysql -u root -p'OLD_ROOT_PW' -e "
CREATE DATABASE IF NOT EXISTS NEW_DB;
CREATE USER IF NOT EXISTS 'NEW_USER'@'%' IDENTIFIED BY 'NEW_PW';
GRANT ALL PRIVILEGES ON NEW_DB.* TO 'NEW_USER'@'%';
FLUSH PRIVILEGES;
"

sudo docker exec alfa_db_1 mysqldump -u root -p'OLD_ROOT_PW' OLD_DB > /tmp/wordpress_backup.sql
sudo docker exec -i alfa_db_1 mysql -u root -p'OLD_ROOT_PW' NEW_DB < /tmp/wordpress_backup.sql
```

If `CREATE USER` fails (user exists):
```bash
sudo docker exec -it alfa_db_1 mysql -u root -p'OLD_ROOT_PW' -e "
ALTER USER 'NEW_USER'@'%' IDENTIFIED BY 'NEW_PW';
GRANT ALL PRIVILEGES ON NEW_DB.* TO 'NEW_USER'@'%';
FLUSH PRIVILEGES;
"
```

### 4b. Only changing user/password (same database)

```bash
sudo docker exec -it alfa_db_1 mysql -u root -p'OLD_ROOT_PW' -e "
ALTER USER 'NEW_USER'@'%' IDENTIFIED BY 'NEW_PW';
GRANT ALL PRIVILEGES ON OLD_DB.* TO 'NEW_USER'@'%';
FLUSH PRIVILEGES;
"
```

### 4c. Changing root password

```bash
sudo docker exec -it alfa_db_1 mysql -u root -p'OLD_ROOT_PW' -e "
ALTER USER 'root'@'localhost' IDENTIFIED BY 'NEW_ROOT_PW';
ALTER USER 'root'@'%' IDENTIFIED BY 'NEW_ROOT_PW';
FLUSH PRIVILEGES;
"
```

---

## 5. Restart

```bash
cd ~/alfa
docker compose down
docker compose up -d
```

---

## 6. Verify

```bash
docker exec alfa_wordpress_1 env | grep WORDPRESS_DB
```

---

## Placeholders

| Placeholder | Meaning | Example |
|-------------|---------|---------|
| OLD_ROOT_PW | Current root password | alfa_root_secure |
| NEW_ROOT_PW | New MYSQL_ROOT_PASSWORD | 123!z2 |
| OLD_DB | Current database name | wordpress |
| NEW_DB | New MYSQL_DATABASE | alfa_db_1 |
| OLD_USER | Current MySQL username | wordpress |
| NEW_USER | New MYSQL_USER | alfa1 |
| NEW_PW | New MYSQL_PASSWORD | 123!z2 |

---

## Troubleshooting

- **Access denied for root:** Try the new password from `.env`.
- **CREATE USER failed:** User exists; use `ALTER USER` instead.
- **Password with `!`:** Use single quotes: `-p'123!z2'`.
