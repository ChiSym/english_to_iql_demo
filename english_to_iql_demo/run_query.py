def run_query(parser, interpreter, query):
    tree = parser.parse(" " + query.strip() + "\n")
    df = interpreter.transform(tree)

    # currently getting some nulls, will investigate 
    return df.drop_nulls()

def run_cols_query(parser, interpreter, query):
    # TODO:
    raise NotImplementedError("Column queries not yet implemented.")
