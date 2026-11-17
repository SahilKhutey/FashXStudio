# Database Access Control & Least Privilege Architecture

## 1. Role Taxonomy and Segregation

To prevent accidental data deletion or privilege escalation, each database enforces a strict separation between schema definition (DDL) and application runtime operations (DML):

| Role Identifier | Role Type | Permitted Commands | Explicitly Denied Commands |
| :--- | :--- | :--- | :--- |
| `fashx_<env>_app` | Runtime Application User | `SELECT`, `INSERT`, `UPDATE`, `DELETE` | `CREATE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT` |
| `fashx_<env>_migrator` | Deployment Migration User | `CREATE`, `ALTER`, `DROP`, `REFERENCES`, DDL | Superuser, Cross-database access |
| `fashx_admin` | Master Provisioning Admin | Infrastructure bootstrap & maintenance | Runtime application traffic |

---

## 2. SQL Role Provisioning Script

Run this script as `fashx_admin` while connected to the target database (e.g. `fashx_prod`):

```sql
-- 1. Create Application Role (No DDL, No Superuser)
CREATE ROLE fashx_prod_app WITH
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    PASSWORD '<INJECTED_SECURE_PASSWORD>';

-- 2. Create Migration Role (Schema Owner, DDL Permitted)
CREATE ROLE fashx_prod_migrator WITH
    LOGIN
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOREPLICATION
    PASSWORD '<INJECTED_SECURE_PASSWORD>';

-- 3. Restrict Public Schema
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO fashx_prod_app;
GRANT USAGE, CREATE ON SCHEMA public TO fashx_prod_migrator;

-- Set Schema Ownership
ALTER SCHEMA public OWNER TO fashx_prod_migrator;

-- 4. Grant Runtime DML Rights to Application Role
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO fashx_prod_app;
GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO fashx_prod_app;

-- 5. Enforce Default Privileges on Objects Created by Migrator
ALTER DEFAULT PRIVILEGES FOR ROLE fashx_prod_migrator IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO fashx_prod_app;

ALTER DEFAULT PRIVILEGES FOR ROLE fashx_prod_migrator IN SCHEMA public
    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO fashx_prod_app;
```

---

## 3. Privilege Verification Protocol

### A. Application Role Verification (Should Succeed)
```sql
-- Connect as fashx_prod_app
SELECT current_user, current_database();
SELECT COUNT(*) FROM user_style_profiles;
```

### B. Prohibited DDL Test (Must Fail)
```sql
-- Connect as fashx_prod_app and attempt schema modification
CREATE TABLE public.unauthorized_table (id INT);
-- Expected Result:
-- ERROR: permission denied for schema public
```
