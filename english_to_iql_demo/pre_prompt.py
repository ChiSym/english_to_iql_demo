def make_preamble(constructor):
    return f"""Your goal is to translate user questions into conditional probability statements relating the variables mentioned in the query.

Statements should take the form "{constructor('X','Y')}" where X is one of the following variables and Y one or a list of multiple of the following variables:

- Commute_minutes
- Age
- Total_income
- Race
- Political_ideology
- Religious_inspiration
- Credit_rating
- Education
- Commute_minutes = '(a) no commute'
- Political_ideology = 'Likely Conservative'

The variables X and Y should be closely related to the entities mentioned in the user query.

Here are some examples of user queries and paired translations:

"""

def make_prompt(preamble, example_pairs, eos=None):
    examples = '\n\n'.join([f"Q: {nl}\nA: {fl}{f' {eos}' if eos is not None else ''}" for (nl,fl) in example_pairs]) + "\n\nQ: {user_query}\nA:"
    return preamble + examples  

def make_example_pairs(constructor):
    return [
        ("How does someone's age affect their income?", 
         constructor("Total_income", ["Age"])),
        ("How does someone's credit rating affect whether or not they are conservative?", 
         constructor("Political_ideology='Likely Conservative'", ["Credit_rating"])),
        ("How does someone's credit rating and race affect whether or not they are conservative? ", 
         constructor("Political_ideology='Likely Conservative'", ["Credit_rating", "Race"])),
         ("How does the probability that someone is conservative change by income?",
           constructor("Political_ideology='Likely Conservative'", ["Total_income"])),
    ]

constructor = lambda event, conditioners : f"probability of {event} given {', '.join(conditioners)}"

pre_prompt = make_prompt(
    preamble=make_preamble(constructor), 
    example_pairs=make_example_pairs(constructor), 
    eos=None
)