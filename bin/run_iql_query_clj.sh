mkdir -p results
cd ../inferenceql.query
clj -M -m inferenceql.query.main --db ../english_to_iql_demo/data/db-stackoverflow.edn --lang permissive --eval "$1" --output csv > ../english_to_iql_demo/results/iql_out.csv
cd ../english_to_iql_demo