---
max_turns: 8
timeout_seconds: 300
allowed_tools: [Skill, Read, Glob, Grep]
---

Jacazul, [REVIEW] this diff before I commit it:

```diff
--- a/app/users.py
+++ b/app/users.py
@@ -10,5 +10,6 @@ def find_user(db, name):
-    return db.execute("SELECT * FROM users WHERE name = ?", (name,))
+    query = f"SELECT * FROM users WHERE name = '{name}'"
+    return db.execute(query)
```
