
package org.communityapp.data;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

public class DatabaseConnection {

    // Relative path to the SQLite database file
    private static final String DB_URL = "jdbc:sqlite:community_app.db";

    public static Connection getConnection() {
        Connection conn = null;

        try {
            // Open connection to SQLite database file
            conn = DriverManager.getConnection(DB_URL);
            System.out.println("✅ JDBC Connection Successful!");

        } catch (SQLException e) {
            System.err.println("❌ Database Connection Failed: " + e.getMessage());
        }

        return conn;
    }
}
