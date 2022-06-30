import subprocess
VENV_PATH = './wordle-venv'

proc = subprocess.Popen([f'source {VENV_PATH}/bin/activate; python3 ./wordle_lib/bot.py; deactivate'],
    shell=True, executable='/bin/bash')
proc.wait()
print('main.py> Done!')
