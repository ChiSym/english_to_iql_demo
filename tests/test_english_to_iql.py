from english_to_iql_demo.pre_prompt import constructor
from english_to_iql_demo.grammar import grammar
from english_to_iql_demo.english_to_iql import english_query_to_iql
import re

def normalize_string(string):
    return re.sub(r'^\s+', '', re.sub(r"▪|</s>", '', string))

def are_equal_up_to_ws(str1, str2):
    return re.sub(r'\n|\s+', '', str1) == re.sub(r'\n|\s+', '', str2)

def make_test_cases(constructor):
    return [
        ("How does someone's education affect their credit rating?", 
         constructor("Credit_rating", ["Education"])),
        ("What's the relationship between someone's income and how likely they are to be conservative?", 
         constructor("Political_ideology = 'Likely Conservative'", ["Total_income"])),
        ("What's the relationship between someone's income and religiosity how likely they are to be conservative?", 
         constructor("Political_ideology = 'Likely Conservative'", ["Total_income", "Religious_inspiration"])),
        ("What's the relationship between someone's income and race how likely they are to be conservative?", 
         constructor("Political_ideology = 'Likely Conservative'", ["Total_income", "Race"])),
        ("What's the relationship between someone's income and their commute time?", 
         constructor("Commute_minutes", ["Total_income"])),
        ("How does the probability that someone has no commute time change with age?", 
         constructor("Commute_minutes = '(a) no commute'", ["Age"]))
    ]

def test_genparse_backend():    
    test_cases = make_test_cases(constructor)

    for test_case, want in test_cases:
        have = normalize_string(english_query_to_iql(
            user_query=test_case, genparse_url="http://34.122.30.137:8888/infer", grammar=grammar
        ))

        assert are_equal_up_to_ws(have, want), [have, want]