grammar = r"""
start: WS? "probability of" WS (var | bool_expr) WS "given" WS var_list WS EOS
EOS: "▪"
bool_expr: "Commute_minutes" WS? "=" WS? "'(a) no commute'" | "Political_ideology" WS? "=" WS? "'Likely Conservative'"
var_list: var | var ", " var
var: "Commute_minutes" | "Age" | "Total_income" | "Race" | "Political_ideology" | "Religious_inspiration" | "Credit_rating" | "Education"
WS: /[ \n]/
"""