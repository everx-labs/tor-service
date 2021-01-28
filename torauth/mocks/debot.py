import subprocess
import logging
log = logging.getLogger(__name__)


def debot(debot_address, wallet_address, keys_filename, one_time_password):
    proc = subprocess.Popen([
        'tonos-cli',
        'debot',
        'fetch',
        debot_address
    ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    def put(string):
        proc.stdin.write(str.encode(string + '\n'))
        proc.stdin.flush()

    def output_line(n):
        for _ in range(n):
            log.debug(proc.stdout.readline())

    output_line(7)
    put('1')

    output_line(2)
    put(one_time_password)

    output_line(1)
    put(keys_filename)

    output_line(2)
    put(wallet_address)

    output_line(2)
    put(keys_filename)

    output_line(1)
    result = proc.stdout.readline().decode("utf-8")

    proc.stdin.close()
    proc.stdout.close()
    proc.stderr.close()
    proc.terminate()
    proc.wait(timeout=1)

    return bool(result == 'Transaction succeeded.\n')
