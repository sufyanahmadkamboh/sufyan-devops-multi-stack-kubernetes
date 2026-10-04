package lab.bookshop;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class BookshopApplication {

    public static void main(String[] args) {
        // The contract: a missing database password is a configuration error. Say so clearly and stop,
        // instead of starting an API that fails on every request.
        String password = System.getenv("DB_PASSWORD");
        if (password == null || password.isBlank()) {
            System.out.println("FATAL java-api: environment variable DB_PASSWORD is not set; refusing to start");
            System.exit(1);
        }
        SpringApplication.run(BookshopApplication.class, args);
    }
}
