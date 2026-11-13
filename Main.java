import java.util.Scanner;
public static void main(String napstablook[]){
    Scanner input = new Scanner(System.in);
    LegacyUser london = new LegacyUser();

    System.out.print("What is your email: ");
    String email = input.nextLine();
    london.setEmail(email);
    System.out.println(london.getEmail());
}