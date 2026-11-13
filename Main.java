
import java.util.ArrayList;

public class Main {

    public static void main(String[] args) {

        // Lesson 3: Retrieve database records as Java objects
        System.out.println("=== USERS FROM DATABASE ===");

        ArrayList<LegacyUser> users = UserDAO.getAllUsers();

        for (LegacyUser user : users) {
            System.out.println(user);
        }

        // Scenario A: Existing database user
        LegacyUser existingUser = new LegacyUser(
            101,
            "london",
            "secure_hash_123",
            "london@email.com",
            "member"
        );

        // Scenario B: Brand-new signup
        LegacyUser newUser = new LegacyUser(
            "alex_dev",
            "hash_secure_991823",
            "alex@tech.org",
            "admin"
        );

        // Scenario C: Default constructor
        LegacyUser emptyUser = new LegacyUser();

        System.out.println("--- Existing User ---");
        System.out.println(existingUser);

        System.out.println("\n--- New Signup ---");
        System.out.println(newUser);

        System.out.println("\n--- Empty User ---");
        System.out.println(emptyUser);
    }
}
