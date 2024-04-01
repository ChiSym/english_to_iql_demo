pre_prompt = """
You have access to an IQL table named developer_records with the following columns:
SalaryUSD, Gender, Ethnicity, YearsCodeProfessional, Background.
Here are a few example instructions and their corresponding IQL queries:

Instruction: Show me 5 rows from the data.

Query: 
SELECT * FROM developer_records LIMIT 5

Instruction: Show me developers' salary, gender, and ethnicity

Query: 
SELECT SalaryUSD, Gender, Ethnicity FROM developer_records

Instruction: List the 10 most frequent gender and ethnicity pairs

Query: 
SELECT
  COUNT(*) AS n,
  Gender,
  Ethnicity
FROM developer_records
GROUP BY Gender, Ethnicity
ORDER BY n DESC
LIMIT 10

Instruction: Show me the probability of developers' salaries given their gender
Query: 

SELECT
  SalaryUSD,
  Gender,
  PROBABILITY OF SalaryUSD
    UNDER developer_record_generator
      GIVEN Gender
        AS probability_salary
FROM developer_records

Instruction: Show me the probability of developers' salaries given their ethnicity

Query: 
SELECT
  SalaryUSD,
  Ethnicity,
  PROBABILITY OF SalaryUSD
    UNDER developer_record_generator
      GIVEN Ethnicity
        AS probability_salary
FROM developer_records

Instruction: Show me developers gender, ethnicity, and how likely they are to be underpaid based on their experience and background

Query:
  SELECT
    PROBABILITY OF SalaryUSD >  SalaryUSD
      UNDER developer_record_generator
        GIVEN YearsCodeProfessional AND Background
        AS probability_underpaid,
    Gender,
    Ethnicity
    FROM
    SELECT * FROM developer_records

Instruction: {user_query}

Query:
SELECT"""
