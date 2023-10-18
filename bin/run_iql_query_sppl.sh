#!/bin/sh
mkdir -p results 
cd ../inferenceql.query
nix develop github:inferenceql/inferenceql.gpm.sppl -c clj -M -m inferenceql.query.main --db ../english_to_iql_demo/data/db-stackoverflow-sppl.edn --lang permissive