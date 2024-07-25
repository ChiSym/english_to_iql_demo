import json
import yaml

def pre_prompt_dispatch(grammar_path):
    if grammar_path == "us_lpm_prob.lark":
        with open("schema.json", "r", encoding="utf-8") as f:
            schema = json.load(f)
        return make_prob_pre_prompt(schema)
    elif grammar_path == "us_lpm_cols.lark":
        with open("us_lpm.json", "r", encoding="utf-8") as f:
            datadict = yaml.dump(json.loads(f.read()))
        return make_cols_pre_prompt(datadict)
    else:
        raise NotImplementedError(f"Preprompt constructor not yet defined for {grammar_path}.")


def make_prob_pre_prompt(schema):
    constructor = lambda event, conditioners : f"probability of {event} given {', '.join(conditioners)}"

    def make_preamble(constructor):
        return f"""Your goal is to translate user questions into conditional probability statements relating the variables mentioned in the query.


Statements should take the form "{constructor('X','Y')}" where X is one of the following variables and Y one or a list of multiple variables. The grammar used is the following:

```
{schema}
```

The variables X and Y should be closely related to the entities mentioned in the user query.

If the answer is not about probabilities, you can type "I can't answer that".

Here are some examples of user queries and paired translations:

"""

    def make_example_pairs(constructor):
        return [
            ("How does someone's age affect their income?", 
            constructor("Total_income", ["Age"])),
            ("What are variables related to income?",
             "I can't answer that"),
            ("How does someone's credit rating affect whether or not they are conservative?", 
            constructor("Political_ideology = 'Likely Conservative'", ["Credit_rating"])),
            ("How does someone's credit rating and race affect whether or not they are conservative? ", 
            constructor("Political_ideology = 'Likely Conservative'", ["Credit_rating", "Race"])),
            ("Why is the sky grey sometimes?",
            "I can't answer that"),
            ("How does the probability that someone is conservative change by income?",
            constructor("Political_ideology = 'Likely Conservative'", ["Total_income"])),
        ]
    
    def make_prompt(preamble, example_pairs, eos=None):
        examples = '\n\n'.join([f"Q: {nl}\nA: {fl}{f' {eos}' if eos is not None else ''}" for (nl,fl) in example_pairs]) + "\n\nQ: {user_query}\nA:"
        return preamble + examples

    pre_prompt = make_prompt(
        preamble=make_preamble(constructor), 
        example_pairs=make_example_pairs(constructor), 
        eos=None
    )

    return pre_prompt

def make_cols_pre_prompt(datadict):
    preamble = """Your goal is to translate user questions about which variables are present in the model into lists of column names.

Here is the data dictionary containing all the column names and their descriptions:

```
{datadict}
```

Return a series of variables from the selection above.

If the answer is not about listing variables, you can type "I can't answer that".

Here are some examples of user queries and paired translations:

"""

    def make_prompt(preamble, example_pairs, eos=None):
        examples = '\n\n'.join([f"Q: {nl}\nA: {fl}{f' {eos}' if eos is not None else ''}" for (nl,fl) in example_pairs]) + "\n\nQ: {user_query}\nA:"
        return preamble + examples  

    example_pairs = [
        ("What are variables related to income?",
        "Total_income"),
        ("How does someone's age affect their income?",
         "I can't answer that"),
        ("Tell me the variables in the model related to someone's credit rating",
        "Credit_rating"),
        ("Tell me all the variables in the model related to someone's insurace",
        "Health_insurance_coverage, Insurance_health_private, Insurance_health_public, Insurance_via_employer, Insurance_purchased_directly, Insurance_Medicare"),
        ("Why is the sky grey sometimes?",
        "I can't answer that"),
        ("List two variables that could be confounders of the relationship of between Credit_rating and Race",
        "Education, Total_income")
    ]

    pre_prompt = make_prompt(preamble.format(datadict=datadict), example_pairs)
    return pre_prompt
