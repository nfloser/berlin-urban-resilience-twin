FROM eclipse-temurin:21-jre-alpine
ARG JENA_VERSION=6.2.0
RUN apk add --no-cache curl \
    && mkdir -p /fuseki/databases \
    && curl -fsSL "https://repo1.maven.org/maven2/org/apache/jena/jena-fuseki-server/${JENA_VERSION}/jena-fuseki-server-${JENA_VERSION}.jar" -o /fuseki/fuseki.jar
WORKDIR /fuseki
EXPOSE 3030
VOLUME ["/fuseki/databases"]
HEALTHCHECK --interval=10s --timeout=4s --retries=20 CMD wget -q --spider http://localhost:3030/ || exit 1
ENTRYPOINT ["sh", "-c", "mkdir -p /fuseki/databases/resilience && exec java -jar /fuseki/fuseki.jar --tdb2 --loc=/fuseki/databases/resilience --update /resilience"]
