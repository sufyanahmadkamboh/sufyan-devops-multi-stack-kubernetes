# ---- Stage 1: build the JAR with Maven and a full JDK ----------------------------------------------------------
FROM maven:3.9-eclipse-temurin-25-alpine AS build
WORKDIR /src

# Dependencies first: this layer is reused from the cache as long as pom.xml does not change
COPY pom.xml .
RUN mvn -B -q dependency:go-offline

# Then the source code, and the build (tests: none in this small lab app)
COPY src ./src
RUN mvn -B -q package -DskipTests

# ---- Stage 2: only a Java runtime (JRE) and the JAR ------------------------------------------------------------
FROM eclipse-temurin:25-jre-alpine

ARG APP_VERSION=1.0.0
ENV APP_VERSION=${APP_VERSION} \
    PORT=8080

# A dedicated user with a fixed numeric ID (Kubernetes can verify "runAsNonRoot" with a number)
RUN addgroup -S -g 10001 app && adduser -S -D -H -u 10001 -G app app

WORKDIR /app
COPY --from=build /src/target/app.jar app.jar

USER 10001
EXPOSE 8080

# Size the heap from the container's memory limit (75 %), not from the host's memory
ENTRYPOINT ["java", "-XX:MaxRAMPercentage=75", "-jar", "app.jar"]
