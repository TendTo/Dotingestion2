FROM maven:3.5-jdk-8 AS build
WORKDIR /app

COPY ./app/pom.xml .
RUN mvn -f ./pom.xml verify clean

COPY ./app/ .
RUN mvn -f ./pom.xml package

FROM openjdk:8-jre-alpine

WORKDIR /app

COPY --from=build /app/target/docker-kafka-streams-1.0.jar .
COPY data/* .

CMD ["java", "-jar", "docker-kafka-streams-1.0.jar"]
