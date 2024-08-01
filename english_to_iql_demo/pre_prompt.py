import json
import yaml

def pre_prompt_dispatch(grammar_path):
    if grammar_path == "us_lpm_prob.lark":
        with open("schema.json", "r", encoding="utf-8") as f:
            schema = json.loads(f.read())
            schema['var_metadata']['State_PUMA10'] = []
            schema['var_metadata']['Zipcode'] = []

            new_schema_normal = {var: "number" for var in schema['types']['normal']}
            new_schema_cat = {var: schema['var_metadata'][var]['levels']
                if var not in ['Zipcode', 'State_PUMA10', 'Work_industry_sector'] else []
                for var in schema['types']['categorical']}

            schema = new_schema_normal | new_schema_cat
            schema = yaml.dump(schema)
        return make_prob_pre_prompt(schema)
    elif grammar_path == "us_lpm_cols.lark":
        with open("us_lpm.json", "r", encoding="utf-8") as f:
            datadict = yaml.dump(json.loads(f.read()))
        return make_cols_pre_prompt(datadict)
    else:
        raise NotImplementedError(f"Preprompt constructor not yet defined for {grammar_path}.")


def make_prob_pre_prompt(schema):
   
    def constructor(event, conditioners):
        if len(conditioners) == 0:
            return f"probability of {event}"
        else:
            return f"probability of {event} given {', '.join(conditioners)}"

    # edit schema to remove PUMA10 levels, so that we fit the context window


    def make_preamble(constructor):
        return f"""Your goal is to translate user questions into conditional probability statements relating the variables mentioned in the query.


Statements should take the form "{constructor('X','Y')}" where X is one of the following variables and Y one or a list of multiple variables. The variables which can be queried are:

```
{schema}
```

The variables X and Y should be closely related to the entities mentioned in the user query.

If the answer is about variables which are not in the above schema, you should answer "I can't answer that". When deciding whether to answer "I can't answer that", pay attention to the above variables.

Here are some examples of user queries and paired translations:

"""

    def make_example_pairs(constructor):
        return [
            ("How does someone's age affect their income?", 
            constructor("Total_income", ["Age"])),
            ("What is the relationship between occupation and voting?", 
            constructor("Occupation", ["Did_you_vote"])),
            ("What are variables related to income?", "I can't answer that"),
            ("How does someone having covid affect whether or not they are conservative?", 
            constructor("Political_ideology = 'Likely Conservative'", ["I_had_covid_last_year"])),
            ("Relationship between Disability and whether they are not currently in the workforce",
            constructor("Disability", ["Work_industry_sector = 'Not in workforce'"])),
            ("What’s the probability that someone has poor mental health given their location? ", 
            constructor("Mental_health_status = '(d) Fair'", ["State_PUMA10"])),
            ("probability of total income", constructor("Total_income", [])),
            ("What is the probability that someone is white given their location?",
            constructor("Race = 'White'", ["State_PUMA10"])),
            ("Relationship between liking vegatables and being a democrat", "I can't answer that"),
            ("Probability that someone has never served in the military given their political ideology",
            constructor("Military_service = '(d) Never served'", ["Political_ideology "])),
            ("Relationship between support for expanding medicare depending on some's education, given they are a democrat",
            constructor("Policy_support_expanding_medicare", ["Educational_attainment", "Party_allegiance = 'Democrat'"])),
            ("Probability that someone is male and disabled in california",
            constructor("Sex = 'Male' and Disability = 'Yes'", ["State_PUMA10, State = 'California'"])),
        ]
    
    def make_prompt(preamble, example_pairs, eos=None):
        examples = '\n\n'.join([f"Q: {nl}\nA: {fl}{f' {eos}' if eos is not None else ''}" for (nl,fl) in example_pairs]) + "\n\nQ: {user_query}\nA:"
        return preamble + examples

    pre_prompt = make_prompt(
        preamble = make_preamble(constructor), 
        example_pairs = make_example_pairs(constructor), 
        eos = None
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
        ("Which variables are related to someone's insurace",
        "Health Insurance Coverage, Insurance Medicare, Insurance_gov_assisted_medicaid, Life_and_other_personal_insurance"),
        ("Why is the sky grey sometimes?",
        "I can't answer that"),
        ("List two variables that could be confounders of the relationship of between Credit_rating and Race",
        "Education, Total_income"),
        ("What variables are about education?", "Education, Educational_attainment")
    ]

    pre_prompt = make_prompt(preamble.format(datadict=datadict), example_pairs)
    return pre_prompt