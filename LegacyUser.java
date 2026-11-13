//Java
// UNENCAPSULATED / VULNERABLE CLASS
public class LegacyUser {
    private int userId;
    private String username;
    private String passwordHash;
    private String email;
    private String userRole;

    public void setEmail(String email) {
    if (email.contains("@")) {
        this.email = email;
    } else {
        System.err.println("INVALID EMAIL: Update rejected.");
    }
    }

public String getEmail(){
    return email;
}


}

