import pexpect

def get_iql_shell():
    child = pexpect.spawnu('./bin/run_iql_query_sppl.sh')
    child.expect('iql> ')

    # for some reason, the first prompt parses wrong---do it here
    # prompt = "SELECT * FROM developer_records LIMIT 5"
    # iql_run(child, prompt)

    return child

def iql_save(iql, prompt, outfile="results/iql_out.csv"):
    result = iql_run(iql, prompt)
    with open(outfile, "w") as f:
        f.write(result)

def iql_run(iql, prompt):
    iql.sendline(prompt)
    iql.expect('\r\r\niql> ')
    result = iql.before
    result = result.split('[K\r')[-1]
    import ipdb; ipdb.set_trace()
    return result