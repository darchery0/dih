
import java.sql.Connection;
import java.sql.Statement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

import org.communityapp.data.DatabaseConnection;

public class UserDAO {

    public static ArrayList<LegacyUser> getAllUsers() {

        ArrayList<LegacyUser> users = new ArrayList<>();

        String sql = "SELECT * FROM users";

        // Lesson 4: Automatically close database resources
        try (Connection conn = DatabaseConnection.getConnection()) {

            if (conn == null) {
                return users;
            }

            try (
                Statement stmt = conn.createStatement();
                ResultSet rs = stmt.executeQuery(sql)
            ) {

                while (rs.next()) {

                    LegacyUser user = new LegacyUser(
                        rs.getInt("id"),
                        rs.getString("username"),
                        rs.getString("email"),
                        rs.getString("role")
                    );

                    users.add(user);
                }
            }

        } catch (SQLException e) {
            System.err.println("Error retrieving users: " + e.getMessage());
        }

        return users;
    }
}
