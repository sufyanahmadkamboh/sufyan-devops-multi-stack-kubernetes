package lab.bookshop;

import javax.sql.DataSource;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.core.io.ClassPathResource;
import org.springframework.jdbc.datasource.init.ResourceDatabasePopulator;
import org.springframework.stereotype.Component;

/**
 * Creates the books table and the sample rows (schema.sql, data.sql; both idempotent).
 * Tried once at startup; if PostgreSQL is not reachable yet, it is tried again on the next request,
 * so the API never crashes just because it started before the database.
 */
@Component
public class SchemaInitializer implements ApplicationRunner {

    private static final Logger log = LoggerFactory.getLogger(SchemaInitializer.class);
    private final DataSource dataSource;
    private volatile boolean done;

    public SchemaInitializer(DataSource dataSource) {
        this.dataSource = dataSource;
    }

    @Override
    public void run(ApplicationArguments args) {
        try {
            ensure();
        } catch (RuntimeException e) {
            log.warn("database not reachable yet, will retry on the next request: {}", rootMessage(e));
        }
    }

    public void ensure() {
        if (done) {
            return;
        }
        synchronized (this) {
            if (done) {
                return;
            }
            new ResourceDatabasePopulator(new ClassPathResource("schema.sql"), new ClassPathResource("data.sql"))
                    .execute(dataSource);
            done = true;
            log.info("books table ready");
        }
    }

    /** The innermost cause, e.g. "UnknownHostException: postgress": short, and names the real problem. */
    static String rootMessage(Throwable e) {
        Throwable t = e;
        while (t.getCause() != null) {
            t = t.getCause();
        }
        return t.getClass().getSimpleName() + ": " + t.getMessage();
    }
}
