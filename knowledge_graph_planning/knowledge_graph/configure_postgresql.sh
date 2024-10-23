#!/usr/bin/env bash

sudo service postgresql start
schema_path="knowledge_graph_planning/knowledge_graph/schema_postgresql.sql"

sudo -u postgres dropdb knowledge_base --if-exists
sudo -u postgres dropdb knowledge_base_truth --if-exists
sudo -u postgres createdb knowledge_base
sudo -u postgres createdb knowledge_base_truth
sudo -u postgres psql -d knowledge_base -f $schema_path
sudo -u postgres psql -d knowledge_base_truth -f $schema_path
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD 'password'"

# Store the password in a dotfile so we can avoid authentication elsewhere
cat >> ~/.pgpass <<EOF
# hostname:port:database:username:password
localhost:*:knowledge_base:postgres:password
localhost:*:knowledge_base_truth:postgres:password
EOF

chmod 600 ~/.pgpass
