#database-security #authorization #user-permissions #access-control #security-patterns #rbac-implementation #finance-auth

#user-permissions #database-security #access-control #authorization

### **Explaining the Implementation of Role-Based Access Control (RBAC) and Row-Level Security (RLS) for an Escrow Service**

Since you have **merchants and users**, where a **merchant can grant specific resources (permissions) to users**, you need a **fine-grained authorization system**. This can be achieved using:

✅ **Role-Based Access Control (RBAC)** – To define permissions for merchants and users.  
✅ **Row-Level Security (RLS)** – To restrict access to specific **transactions** based on merchant-user relationships.  
✅ **Attribute-Based Access Control (ABAC) (Optional)** – If merchants can add dynamic rules like time-based access or limits.

---

## **1. Data Model for Permissions & Access Control**

### **Tables for Role-Based Access Control (RBAC)**

#### **1. Users Table**

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100),
    email VARCHAR(255) UNIQUE NOT NULL,
    merchant_id INT,
    FOREIGN KEY (merchant_id) REFERENCES merchants(id)
);
```

Each **user** belongs to a **merchant**.

#### **2. Merchants Table**

```sql
CREATE TABLE merchants (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL
);
```

#### **3. Roles Table (Predefined roles like "Merchant Admin", "User")**

```sql
CREATE TABLE roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(50) UNIQUE NOT NULL
);
```

Examples:

- `Merchant Admin` (Can create/view transfers for all users under a merchant).
- `User` (Can only create/view their own transactions).

#### **4. Permissions Table (What actions a role can perform)**

```sql
CREATE TABLE permissions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    action VARCHAR(50) UNIQUE NOT NULL  -- Example: "create_transfer", "view_transfer", "bulk_transfer"
);
```

#### **5. Role-Permission Mapping (Many-to-Many)**

```sql
CREATE TABLE role_permissions (
    role_id INT REFERENCES roles(id),
    permission_id INT REFERENCES permissions(id),
    PRIMARY KEY (role_id, permission_id)
);
```

A role can have multiple permissions.

#### **6. User-Role Mapping (Assigning Roles to Users)**

```sql
CREATE TABLE user_roles (
    user_id INT REFERENCES users(id),
    role_id INT REFERENCES roles(id),
    PRIMARY KEY (user_id, role_id)
);
```

Each **user** has a role (e.g., "Merchant Admin" or "User").

---

## **2. Transactions Table with Row-Level Security (RLS)**

A **transaction belongs to a user, but access should be restricted based on permissions**.

```sql
CREATE TABLE transactions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT REFERENCES users(id),
    merchant_id INT REFERENCES merchants(id),
    amount DECIMAL(10,2),
    type ENUM('single_transfer', 'bulk_transfer'),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Now, we need to **enforce row-level access control** so that:  
✅ A user **can only see transactions belonging to them**.  
✅ A merchant **can view all transactions for their users** (if they have permission).

---

## **3. Implementing Row-Level Security (RLS) Using Views**

A view is used to filter transactions based on permissions.

```sql
CREATE VIEW user_transactions AS
SELECT t.*
FROM transactions t
JOIN users u ON t.user_id = u.id
WHERE u.id = (SELECT id FROM users WHERE email = CURRENT_USER())
OR u.merchant_id = (SELECT merchant_id FROM users WHERE email = CURRENT_USER() AND EXISTS 
    (SELECT 1 FROM user_roles ur 
     JOIN role_permissions rp ON ur.role_id = rp.role_id 
     JOIN permissions p ON rp.permission_id = p.id 
     WHERE ur.user_id = u.id AND p.action = 'view_transfer'));
```

🔹 This ensures that:

- A **user** only sees their own transactions.
- A **merchant** sees all their users' transactions **if they have the `view_transfer` permission**.

---

## **4. Implementing Role-Based Authorization in the Application**

If your database does **not support views**, enforce **RBAC + RLS at the application level**.

### **Example: Middleware for Checking Permissions in Node.js**

```javascript
async function authorize(userId, permission) {
    const result = await db.query(`
        SELECT p.action FROM user_roles ur
        JOIN role_permissions rp ON ur.role_id = rp.role_id
        JOIN permissions p ON rp.permission_id = p.id
        WHERE ur.user_id = ? AND p.action = ?`, 
        [userId, permission]
    );

    return result.length > 0;
}
```

Now, use this function before allowing an action:

```javascript
app.post('/transfer/create', async (req, res) => {
    const userId = req.user.id;
    const hasPermission = await authorize(userId, 'create_transfer');

    if (!hasPermission) {
        return res.status(403).json({ message: "Forbidden" });
    }

    // Proceed with transfer creation
});
```

---

## **5. Implementing Authorization in Django ORM (Python)**

### **Filtering Transactions Based on Roles**

```python
def get_transactions(user):
    if user.has_permission("view_transfer"):
        return Transaction.objects.filter(merchant=user.merchant)
    return Transaction.objects.filter(user=user)
```

🔹 This ensures **users see only their transactions, while merchants (with permission) see all transactions under their business**.

---

## **6. Implementing Multi-Tenancy for Merchants**

To **fully isolate merchants**, enforce **tenant-based filtering**:

### **Using Database Constraints (PostgreSQL/MySQL)**

```sql
ALTER TABLE users ADD CONSTRAINT fk_user_merchant FOREIGN KEY (merchant_id) REFERENCES merchants(id) ON DELETE CASCADE;
```

If a **merchant is deleted**, all related users are removed.

---

## **Final Summary**

### **🔹 What You Implemented**

|**Feature**|**Implementation**|
|---|---|
|✅ **RBAC** (Who can do what?)|**User Roles & Permissions Table**|
|✅ **RLS** (Who can see which transactions?)|**Views + Application Layer Filtering**|
|✅ **Multi-Tenancy**|**Merchant Isolation using Merchant ID**|
|✅ **Access Control in API**|**Middleware checking permissions before actions**|

---

### **🔹 How to Explain This in an Interview?**

💡 **"I implemented a fine-grained authorization system for our escrow service using RBAC and RLS. Each user belongs to a merchant, and merchants can grant specific permissions like creating single transfers or bulk transfers. To enforce this, I designed a role-based access system with a permissions table that maps user actions. Additionally, I implemented row-level security to ensure users can only see transactions they are authorized to access, using SQL views and application-level filtering. This approach ensures secure, scalable multi-tenancy and enforces strict access control."**

Would you like a **real-world example using AWS IAM or Open Policy Agent (OPA) for dynamic access control?** 🚀