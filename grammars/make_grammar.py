# Example usage: python make_grammar.py --schema-path ../schema.json

import os
import json
import argparse
import warnings
from lark import Lark

# categoricals which should be excluded from the grammar entirely
CATEGORICAL_EXCLUSIONS_COLS = []
CATEGORICAL_EXCLUSIONS_PROB = []
# categoricals which cannot be in an assignment clause
CATEGORICAL_ASSIGNMENT_EXCLUSIONS_PROB = ['State_PUMA10']
CATEGORICAL_ASSIGNMENT_EXCLUSIONS_COLS = []

NORMAL_EXCLUSIONS = []

prob_grammar_template = """start: query_wrapper EOS
query_wrapper: prob_clause " using ChiExpert" -> chiexpert
| prob_clause " using data" -> data
| prob_clause " using GLM" -> glm
| "I can't answer that"
prob_clause: " probability of " sample_variable 
| " probability of " sample_variable ", " sample_variable
| " probability of " sample_variable " given " condition_variable
| " probability of " sample_variable ", " sample_variable " given " condition_assignment
| " probability of " sample_variable ", " sample_variable " given " condition_assignment ", " condition_assignment
| " probability of " sample_variable " given " condition_assignment
| " probability of " sample_variable " given " condition_assignment ", " condition_variable
| " probability of " sample_variable " given " condition_variable ", " condition_assignment
| " probability of " sample_variable " given " condition_assignment ", " condition_assignment
| " probability of " sample_assignment " given " condition_variable
| " probability of " sample_assignment " given " condition_variable ", " condition_variable
| " probability of " sample_assignment " given " condition_assignment ", " condition_variable
| " probability of " sample_assignment " given " condition_variable ", " condition_assignment
EOS: "\\n"
BOOL_EXPR: " and " | " or "
sample_assignment: assignment
condition_assignment: assignment
sample_variable: variable
condition_variable: variable
assignment: {assignment}
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

def make_grammar_symbols(
    schema, categorical_exclusions, categorical_assignment_exclusions, normal_exclusions
):
    normals = [x for x in schema["types"]["normal"]]
    categoricals = [x for x in schema["types"]["categorical"]]

    n_n = range(len(normals))
    n_c = range(len(categoricals))

    categorical_values = []
    categorical_var_names = []
    categorical_assignments = []
    categorical_variable_nts = []
    for i, var in enumerate(categoricals):
        if var not in categorical_exclusions:
            nt = f"CATEGORICAL{i}"
            categorical_variable_nts.append(nt)
            categorical_var_names.append(f"{nt}: \"{var}\"")
            if var not in categorical_assignment_exclusions:
                categorical_assignments.append(f"{nt} OPERATOR {nt}_VAL")
                prefix = f"{nt}_VAL: " 
                levels = [f"\"\'{level}\'\""
                    for level in schema["var_metadata"][var]["levels"]]
                levels = "\n\t| ".join(levels)
                categorical_values.append(prefix + levels)

    normal_variable_nts = []
    normal_var_names = []
    normal_assignments = []
    normal_ineq_assignments = []
    for i, var in enumerate(normals):
        if var not in normal_exclusions:
            nt = f"NORMAL{i}"
            normal_variable_nts.append(nt)
            normal_var_names.append(f"{nt}: \"{var}\"")
            normal_assignments.append(f"{nt} OPERATOR NORM_DIGIT")
            normal_ineq_assignments.append(f"{nt} INEQUALITY NORM_DIGIT")

    
    var_nonterminals = normal_variable_nts + categorical_variable_nts
    var_names = normal_var_names + categorical_var_names
    assignments = normal_assignments + categorical_assignments

    return (
        assignments,
        categorical_values,
        var_names,
        var_nonterminals,
        categorical_assignments,
        normal_ineq_assignments,
    )

def get_grammar_names(col, schema):
    if col in schema["types"]["normal"]:
        return f"NORMAL{schema['types']['normal'].index(col)}"
    elif col in schema["types"]["categorical"]:
        return f"CATEGORICAL{schema['types']['categorical'].index(col)}"
    else:
        raise ValueError(f"Unrecognized column {col}")

def make_grammars(schema_path):
    schema = json.load(open(schema_path, 'r'))

    (assignment, categorical_values, var_names, var_nonterminals, categorical_assignment, normal_ineq_assignment) = make_grammar_symbols(
        schema, CATEGORICAL_EXCLUSIONS_PROB, CATEGORICAL_ASSIGNMENT_EXCLUSIONS_PROB, NORMAL_EXCLUSIONS
    )

    us_lpm_prob = prob_grammar_template.format(
        assignment="\n\t| ".join(assignment),
        categorical_values="\n".join(categorical_values),
        var_names="\n".join(var_names),
        var_nonterminals="\n\t| ".join(var_nonterminals),
        categorical_assignment= "\n\t| ".join(categorical_assignment),
        continuous_ineq_assignment="\n\t| ".join(normal_ineq_assignment),
    )

    (_, _, var_names, var_nonterminals, _, _) = make_grammar_symbols(
        schema, CATEGORICAL_EXCLUSIONS_COLS, CATEGORICAL_ASSIGNMENT_EXCLUSIONS_COLS, NORMAL_EXCLUSIONS
    )

    us_lpm_cols = cols_grammar_template.format(
        var_names="\n".join(var_names),
        var_nonterminals="\n\t| ".join(var_nonterminals),
    )

    return us_lpm_prob, us_lpm_cols

prob_test_sentences = [
    " probability of Age using ChiExpert",
    " probability of Age given Family_income using data",
    " probability of Age = -2 given Family_income using GLM",
    " probability of Age = -2 given Family_income, Race using ChiExpert",
    " probability of Age = -2 given Family_income, Race = 'White' using data",
    " probability of Family_income given Age = 0, Race using GLM",
    " probability of Family_income given Race, Age = 2 using ChiExpert",
    " probability of Family_income given Age = 0, Race = 'White' using GLM",
    " probability of Race = 'White' given State_PUMA10 using data",
    " probability of Race, Family_income using ChiExpert"
]

cols_test_sentences = [
    " Age",
    " Age, Family_income",
    " Age, Family_income, Race"
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

    schema_path = os.path.abspath(args.schema_path)
    output_dir = os.path.abspath(args.output_dir) if args.output_dir else os.getcwd()

    prob_grammar, cols_grammar = make_grammars(args.schema_path)
    
    test_grammar(prob_grammar, prob_test_sentences)
    test_grammar(cols_grammar, cols_test_sentences)

    with open(os.path.join(args.output_dir, 'us_lpm_prob.lark'), 'w+') as f:
        f.write(prob_grammar)

    with open(os.path.join(args.output_dir, 'us_lpm_cols.lark'), 'w+') as f:
        f.write(cols_grammar)