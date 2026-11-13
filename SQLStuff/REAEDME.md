## Running the SQL Files

The project uses SQLite 3 and can be executed through the terminal in GitHub Codespaces.

### Prerequisites

* GitHub Codespaces
* SQLite 3 installed in the environment

### Execution Instructions

1. Open the project in GitHub Codespaces.

2. Open the terminal.

3. Navigate to the directory containing the SQL files:

   ```bash
   cd SQLStuff
   ```

4. Run the main SQL script:

   ```bash
   sqlite3 main.db < main.sql
   ```

   This executes the `main.sql` script against the `main.db` database. The script loads the schema and sample data through its `.read` commands, then runs the three test queries.

5. Review the terminal output to verify that the tables were populated and the queries returned results.

### Alternative Execution

To open the SQLite interactive shell:

```bash
sqlite3 main.db
```

Then execute the main script from inside the SQLite shell:

```sql
.read main.sql
```

To exit the shell:

```sql
.quit
```

### Important Notes

* Run these commands from the `SQLStuff` directory because `main.sql` references `schema.sql` and `seed_data.sql` using relative paths.
* The `main.sql` script executes `schema.sql`, which drops and recreates the existing tables before inserting sample data. Running it again will reset those tables and repopulate them with the seed data.
* The database file `main.db` is created automatically if it does not already exist.
* The main script enables foreign-key enforcement before loading the schema and data.
