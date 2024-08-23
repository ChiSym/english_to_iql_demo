import argparse
import json
import os
import warnings
from lark import Lark


CATEGORICAL_EXCLUSIONS_COLS = ['Zipcode']
CATEGORICAL_EXCLUSIONS_PROB = ['Zipcode', 'State_PUMA10']
NORMAL_EXCLUSIONS = []

# we'll want to change expr to only take Census/PUMS variables
prob_grammar_template = """start: " probability of " variable EOS
| " probability of " variable " given " variable EOS
| " probability of " variable " given " assignment EOS 
| " probability of " variable " given " assignment ", " variable EOS
| " probability of " variable " given " variable ", " assignment EOS
| " probability of " variable " given " assignment ", " assignment EOS
| " probability of " assignment " given " variable EOS
| " probability of " assignment " given " variable ", " variable EOS
| " probability of " assignment " given " assignment ", " variable EOS
| " probability of " assignment " given " variable ", " assignment EOS
| " probability of " expr " given State_PUMA10" [", State = " CATEGORICAL0_VAL] [", " geo_assignment] "\\n" -> geo
| " I can't answer that" EOS
EOS: "\\n"
expr: geo_assignment 
    | geo_assignment BOOL_EXPR geo_assignment
    | geo_assignment BOOL_EXPR geo_assignment BOOL_EXPR geo_assignment
    | geo_assignment BOOL_EXPR geo_assignment BOOL_EXPR geo_assignment BOOL_EXPR geo_assignment
BOOL_EXPR: " and " | " or "
assignment: {assignment}
geo_assignment: continuous_ineq_assignment | categorical_assignment
continuous_ineq_assignment: {continuous_ineq_assignment}
categorical_assignment: {categorical_assignment}
variable: {var_nonterminals}
{var_names}
{categorical_values}
OPERATOR: "=" | " = "
INEQUALITY: " > " | " < "
NORM_DIGIT: "-2" | "-1" | "0" | "1" | "2"
DIGIT: "0".."9"
INT: DIGIT+
FLOAT: INT "." INT? | "." INT
NUMBER: FLOAT | INT"""

cols_grammar_template = """start: " " var_list EOS | " I can't answer that\\n"
EOS: "\\n"
var_list: var | var ", " var | var ", " var ", " var | var ", " var ", " var ", " var | var ", " var ", " var ", " var ", " var
var: {var_nonterminals}
{var_names}
"""

def make_grammar_symbols(schema, categorical_exclusions, normal_exclusions):
    normals = [x for x in schema["types"]["normal"]]
    categoricals = [x for x in schema["types"]["categorical"]]

    n_n = range(len(normals))
    n_c = range(len(categoricals))
    normal_variable_nts = [f"NORMAL{i}" for i, var in enumerate(normals) if var not in normal_exclusions]
    categorical_variable_nts = [f"CATEGORICAL{i}" for i, var in enumerate(categoricals) 
        if var not in categorical_exclusions]
    var_nonterminals = normal_variable_nts + categorical_variable_nts
    normal_var_names = [
        f"NORMAL{i}: \"{var}\"" for i, var in enumerate(normals) if var not in normal_exclusions
    ]
    categorical_var_names = [
        f"CATEGORICAL{i}: \"{var}\"" for i, var in enumerate(categoricals)  if var not in categorical_exclusions
    ]
    var_names = normal_var_names + categorical_var_names

    # normal currently a hack for age only to make it easier for genparse
    normal_assignment = [f"{nt} OPERATOR NORM_DIGIT" for nt in normal_variable_nts]
    normal_ineq_assignment = [f"{nt} INEQUALITY NORM_DIGIT" for nt in normal_variable_nts]
    categorical_assignment = [f"{nt} OPERATOR {nt}_VAL" for nt in categorical_variable_nts]
    assignment = normal_assignment + categorical_assignment

    categorical_values = []
    for i, var in enumerate(categoricals):
        if var not in categorical_exclusions:
            prefix = f"CATEGORICAL{i}_VAL: " 
            levels = [f"\"\'{level}\'\""
                for level in schema["var_metadata"][var]["levels"]]
            levels = "\n\t| ".join(levels)
            categorical_values.append(prefix + levels)

    return (
        assignment,
        categorical_values,
        var_names,
        var_nonterminals,
        categorical_assignment,
        normal_ineq_assignment,
    )

def get_grammar_names(col, schema):
    if col in schema["types"]["normal"]:
        return f"NORMAL{schema['types']['normal'].index(col)}"
    elif col in schema["types"]["categorical"]:
        return f"CATEGORICAL{schema['types']['categorical'].index(col)}"
    else:
        raise ValueError(f"Unrecognized column {col}")

def make_grammars(schema_path):
    # at most 2 free variables
    schema = json.load(open(schema_path, 'r'))
    #census_cols = json.load(open(census_cols_path, 'r'))
    #census_grammar_names = [
    #    get_grammar_names(census_col, schema)
    #    for census_col in census_cols]

    (assignment, categorical_values, var_names, var_nonterminals, categorical_assignment, normal_ineq_assignment) = make_grammar_symbols(
        schema, CATEGORICAL_EXCLUSIONS_PROB, NORMAL_EXCLUSIONS
    )

    #census_assignment = [a for a in assignment 
    #    if a.split(" ")[0] in census_grammar_names]

    us_lpm_prob = prob_grammar_template.format(
        assignment="\n\t| ".join(assignment),
        categorical_values="\n".join(categorical_values),
        var_names="\n".join(var_names),
        var_nonterminals="\n\t| ".join(var_nonterminals),
        categorical_assignment= "\n\t| ".join(categorical_assignment),
        continuous_ineq_assignment="\n\t| ".join(normal_ineq_assignment),
       #census_assignment="\n\t| ".join(census_assignment),
    )

    (_, _, var_names, var_nonterminals, _, _) = make_grammar_symbols(
        schema, CATEGORICAL_EXCLUSIONS_COLS, NORMAL_EXCLUSIONS
    )

    us_lpm_cols = cols_grammar_template.format(
        var_names="\n".join(var_names),
        var_nonterminals="\n\t| ".join(var_nonterminals),
    )

    return us_lpm_prob, us_lpm_cols

prob_test_sentences = [
    " probability of Age",
    " probability of Age given Total_income",
    " probability of Age = -2 given Total_income",
    " probability of Age = -2 given Total_income, Race",
    " probability of Age = -2 given Total_income, Race = 'White'",
    " probability of Total_income given Age = 0, Race",
    " probability of Total_income given Race, Age = 2",
    " probability of Total_income given Age = 0, Race = 'White'",
    " probability of Race = 'White' given State_PUMA10",
]

cols_test_sentences = [
    " Age",
    " Age, Total_income",
    " Age, Total_income, Race",
    " State_PUMA10"
]

def test_grammar(grammar, test_sentences):
    l = Lark(grammar)

    for sentence in test_sentences:
        try:
            l.parse(sentence + "\n")
        except Exception as e:
            warnings.warn(
                f'Failed to parse {sentence} with {e}. There may be a problem with this grammar.'
            )


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--schema-path', help='Path to grammar schema')
    parser.add_argument('--output-dir', help='Path to output grammar dir', default='')

    args = parser.parse_args()

    prob_grammar, cols_grammar = make_grammars(args.schema_path)
    
    test_grammar(prob_grammar, prob_test_sentences)
    test_grammar(cols_grammar, cols_test_sentences)

    with open(os.path.join(args.output_dir, 'us_lpm_prob.lark'), 'w+') as f:
        f.write(prob_grammar)

    with open(os.path.join(args.output_dir, 'us_lpm_cols.lark'), 'w+') as f:
        f.write(cols_grammar)