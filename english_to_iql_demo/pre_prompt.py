pre_prompt = """
### IQL table with properties
# data(SalaryUSD, Gender, Ethnicity, YearsCodeProfessional, Background)
# Stackoverflow Developer Survey
# Explore the developer records
SELECT * FROM developer_records LIMIT 5
# Show me developers' salary, gender, and ethnicity
SELECT SalaryUSD, Gender, Ethnicity FROM developer_records
# List the 10 most frequent gender and ethnicity pairs
SELECT
  COUNT(*) AS n,
  Gender,
  Ethnicity
FROM developer_records
GROUP BY Gender, Ethnicity
ORDER BY n DESC
LIMIT 10
# Show me the probability of developers' salaries given their gender
SELECT
  SalaryUSD,
  Gender,
  PROBABILITY OF SalaryUSD
    UNDER developer_record_generator
      GIVEN Gender
        AS probability_salary
FROM developer_records
# Show me the probability of developers' salaries given their ethnicity
SELECT
  SalaryUSD,
  Ethnicity,
  PROBABILITY OF SalaryUSD
    UNDER developer_record_generator
      GIVEN Ethnicity
        AS probability_salary
FROM developer_records
# Show me developers gender, ethnicity, and how likely they are to be underpaid based on their experience and background
  SELECT
    PROBABILITY OF SalaryUSD >  SalaryUSD
      UNDER developer_record_generator
        GIVEN YearsCodeProfessional AND Background
        AS probability_underpaid,
    Gender,
    Ethnicity
    FROM
    SELECT * FROM developer_records
# {user_query}
SELECT"""