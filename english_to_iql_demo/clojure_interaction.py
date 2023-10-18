import pexpect

def get_iql_shell():
    child = pexpect.spawnu('./bin/run_iql_query_sppl.sh', timeout=200)
    child.expect('iql> ')

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
    result = result.replace('\r\r\n', '\n')
    return result