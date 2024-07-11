docker run \
    -itd \
    -p 7474:7474 -p 7687:7687 \
    --env NEO4J_AUTH=neo4j/yourneo4jpassword \
    --name dozerb-apoc \
    --env NEO4J_PLUGINS='["apoc"]' \
    --env NEO4J_apoc_export_file_enabled=true \
    --env NEO4J_apoc_import_file_enabled=true \
    --env NEO4J_apoc_import_file_useneo4jconfig=true \
    --env NEO4J_dbms_security_procedures_unrestricted=algo.,apoc. \
    --env NEO4J_dbms_security_procedures_allowlist=apoc.* \
    graphstack/dozerdb:5.20.0.0-alpha.1