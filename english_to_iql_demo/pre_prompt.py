pre_prompt = """
You have access to an IQL table named data with the following columns:
"Commute_minutes" | "Age" | "Total_income" | "Race" | "Political_ideology" | "Religious_inspiration" | "Credit_rating" | "Education"
Your goal is to write a query given an instruction. A query can have one of two forms: 

Form 1:
SELECT 
PROBABILITY OF <variable> UNDER lpm GIVEN <variables>,
<variables>
FROM (
SELECT
<variable>, <variables>
GROUP BY <variable>, <variables>
)

Form 2:
SELECT 
PROBABILITY OF <variable> = <value> UNDER lpm GIVEN <variables>,
<variables>
FROM (
SELECT
<variables>
GROUP BY <variables>
)

Here are some example instructions and corresponding queries:

Instruction: 

How does someone's age affect their income?

Query: 

SELECT
PROBABILITY OF Total_income UNDER lpm GIVEN Age AS p,
Total_income,
Age
FROM (
SELECT 
Total_income, Age
FROM data
GROUP BY Total_income, Age
)

Instruction: 

How does someone's credit rating affect whether or not they are conservative? 

Query:

SELECT
PROBABILITY OF Political_ideology = 'Likely Conservative' UNDER lpm GIVEN Credit_rating AS p,
Credit_rating
FROM (
SELECT 
Credit_rating
FROM data
GROUP BY Credit_rating
)

Instruction: 

How does someone's credit rating and race affect whether or not they are conservative? 

Query:

SELECT
PROBABILITY OF Political_ideology = 'Likely Conservative' UNDER lpm GIVEN Credit_rating AND Race AS p,
Credit_rating,
Race
FROM (
SELECT 
Credit_rating, Race
FROM data
GROUP BY Credit_rating, Age
)

Now, the user will write an instruction and the IQL query will be generated. DO NOT ADD UNNECESSARY VARIABLES TO THE QUERY---for example, if the user asks about how race affects the probability of someone being conservative, you should not include age in the query.

Instruction:

{user_query}

Query:

"""
