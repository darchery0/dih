
public class LegacyUser {

    // Private instance variables
    private int userId;
    private String username;
    private String passwordHash;
    private String email;
    private String userRole;

    // 1. Default constructor
    public LegacyUser() {
    }

    // 2. Full DB Record constructor
    public LegacyUser(int userId, String username,
                      String passwordHash, String email,
                      String userRole) {

        setUserId(userId);
        setUsername(username);
        setPasswordHash(passwordHash);
        setEmail(email);
        setUserRole(userRole);
    }

    // 3. New Signup constructor (without userId)
    public LegacyUser(String username,
                      String passwordHash, String email,
                      String userRole) {

        setUsername(username);
        setPasswordHash(passwordHash);
        setEmail(email);
        setUserRole(userRole);
    }

    // Constructor for database records without password hash
public LegacyUser(int userId, String username,
                  String email, String userRole) {

    setUserId(userId);
    setUsername(username);
    setEmail(email);
    setUserRole(userRole);
}

    // Getters
    public int getUserId() {
        return userId;
    }

    public String getUsername() {
        return username;
    }

    public String getPasswordHash() {
        return passwordHash;
    }

    public String getEmail() {
        return email;
    }

    public String getUserRole() {
        return userRole;
    }

    // Setters with validation
    public void setUserId(int userId) {
        if (userId > 0) {
            this.userId = userId;
        } else {
            System.err.println("INVALID USER ID: ID must be positive.");
        }
    }

    public void setUsername(String username) {
        if (username != null && !username.trim().isEmpty()) {
            this.username = username.trim();
        } else {
            System.err.println("INVALID USERNAME: Username cannot be empty.");
        }
    }

    public void setPasswordHash(String passwordHash) {
        if (passwordHash != null && !passwordHash.trim().isEmpty()) {
            this.passwordHash = passwordHash;
        } else {
            System.err.println("INVALID PASSWORD HASH: Hash cannot be empty.");
        }
    }

    public void setEmail(String email) {
        if (email != null &&
            email.trim().matches("^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$")) {
            this.email = email.trim();
        } else {
            System.err.println("INVALID EMAIL: Update rejected.");
        }
    }

    public void setUserRole(String userRole) {
        if (userRole != null && !userRole.trim().isEmpty()) {
            this.userRole = userRole.trim();
        } else {
            System.err.println("INVALID USER ROLE: Role cannot be empty.");
        }
    }

    // toString()
    @Override
    public String toString() {
        return "User [" +
                "ID=" + userId +
                ", Username='" + username + '\'' +
                ", Email='" + email + '\'' +
                ", Role='" + userRole + '\'' +
                ']';
    }
}
