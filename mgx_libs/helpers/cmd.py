import subprocess as sp


def run_cmd(s, shell=False):
    try:

        cmd = s.split(" ")
        if shell:
            cmd = s

        with sp.Popen(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=shell) as cmd:

            stdout, stderr = [i.decode('utf8') for i in cmd.communicate()]
            if cmd.returncode != 0:
                return (1, stdout + stderr)

            return (0, stdout)

    except Exception as e:
        return (1, str(e))
