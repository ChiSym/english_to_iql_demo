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
        return f"""Your goal is to translate user questions into conditional probability statements relating the variables mentioned in a query.


Statements should take the form "{constructor('X','Y')}" where X is one of the following variables and Y one or a list of multiple variables. The variables which can be queried are related to the US population:

```
{schema}
```

The variables X and Y should be closely related to the entities mentioned in the user query. 

Numerical variables can take on -2 (very low); -1 (low); 0 (average); 1 (high) and 2 (very high).

If the answer is about variables which are not in the above schema, you should answer "I can't answer that".

Here are some examples of user queries and paired translations:

"""

    def make_example_pairs(constructor):
        return [
            ("How does someone's age affect their income?", 
            constructor("Total_income", ["Age"])),
            ("Show me the probability of recent social media use given occupation", 
            constructor("Used_social_media_in_part_24hrs", ["Occupation"])),
            ("What are variables related to income?", "I can't answer that"),
            ("How does a voter having covid affect whether or not they had to borrow money from family for an emergency?", 
            constructor("Pay_for_emergency_by_borrowing_from_friends = 'Yes'", ["I_had_covid_last_year"])),
            ("Find the relationship between disability and whether a voter is not currently in the workforce",
            constructor("Disability", ["Employment_status = 'Not in workforce'"])),
            ("What’s the probability that someone is registered to vote given their location? ", 
            constructor("Registered_to_vote = 'Yes'", ["State_PUMA10"])),
            ("Show me the probability that a voter is white given their location?",
            constructor("Race = 'White'", ["State_PUMA10"])),
            ("Relationship between liking vegatables and being a democrat", "I can't answer that"),
            ("find the probability of high-income rural voters by location",
            constructor("Total_income > 1 and Environment = 'Rural'", ["State_PUMA10"])),
            ("Show me the probability of support for expanding medicare depending on some's party allegiance, given they are a non-college educated",
            constructor("Policy_support_expanding_medicare", ["Educational_attainment = '(b) High school graduate'", "Party_allegiance"])),
            ("Probability that a voter is democrat and disabled in california",
            constructor("Party_allegiance = 'Democrat' and Disability = 'Yes'", ["State_PUMA10, State = 'California'"])),
            ("Shoe mw the probability of poor white voters by location",
            constructor("Total_income < 0 and Race = 'White'", ["State_PUMA10"]))
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
        ("What are variables related to income?", "Total_income"),
        ("How does someone's age affect their income?", "I can't answer that"),
        ("Tell me the variables in the model related to someone's credit rating", "Credit_rating"),
        ("Which variables are related to someone's insurace",
        "Health Insurance Coverage, Insurance Medicare, Insurance_gov_assisted_medicaid, Life_and_other_personal_insurance"),
        ("Why is the sky grey sometimes?",
        "I can't answer that"),
        ("Show me variables related to language",
        "English_fluency, Language_spoken_at_home"),
        ("What variables are about education?", "Education, Educational_attainment")
    ]

    pre_prompt = make_prompt(preamble.format(datadict=datadict), example_pairs)
    return pre_prompt