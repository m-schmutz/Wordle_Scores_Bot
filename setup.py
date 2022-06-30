import subprocess
import wordle_lib.ansi as ansi

VENV_PATH = './wordle-venv'
VENV_CREATE_SHCMD = f'python3 -m venv {VENV_PATH}'
PIP_NAMES = 'opencv-python pytesseract requests discord psutil'

#region
# def time_ns_str():
#     t = str(time.time_ns())
#     return f'[{t[:-9]}.{t[-9:]}]'

# def install_apt_packages() -> None:
#     # record apt packages that were actually installed
#     # !!! DO NOT INCLUDE PACKAGES WHICH WERE ALREADY INSTALLED !!!
#     # apt_installs = open('new.apt', 'w')
#     # apt_installs.close()

#     # Create a pipe and launch a subprocess.
#     rfd, wfd = os.pipe()
#     proc     = Popen([f'sudo apt-get -y install {" ".join(APT_PACKAGES)}'], shell=True, stdout=wfd)
#     os.close(wfd)

#     # Continuously parse the subprocess's output untill it completes.
#     lineno = 0
#     raw_output = []
#     log = open('apt_install.log', 'w')
#     log.write(f'{time_ns_str()} Polling...\n')
#     proc_output = os.fdopen(rfd, 'r', newline='')
#     while proc.poll() == None:
#         # Get next line
#         line = proc_output.readline()
#         t_now = time_ns_str()
#         line_writeable = line.encode("unicode_escape").decode()
#         raw_output.append(line)
#         lineno += 1
        
#         # Update log and terminal
#         log.write(f'{t_now}{lineno:>4}: \'{line_writeable}\'\n')
#         print('# lines processed:', lineno, end='\r')

#     # Close process and log stream
#     proc_output.close()
#     log.close()

#     # Create the virtual environment.
#     print('\nCreating virtual environment...', end=' ')
#     proc = Popen([VENV_CREATE_SHCMD], shell=True)
#     proc.wait()
#     print('Done!')

#     return ''.join(raw_output)
#endregion

def _remove_apt_packages() -> None:
    # remove the venv diectory.
    # (this includes all pip packages).
    subprocess.run([f'rm -r {VENV_PATH}'],
        shell=True)

    # remove virtual environment package.
    # (this should be the only package that was added system wide).
    subprocess.run([f'sudo apt-get -y purge python3-venv virtualenv'],
        shell=True)

    # clean up.
    # clear cache, remove unrequired packages, fix any failed/broken installs.
    subprocess.run(['sudo apt-get clean'],
        shell=True)
    subprocess.run(['sudo apt-get -y autoremove'],
        shell=True)
    subprocess.run(['sudo apt-get -y -f install'],
        shell=True)

    return

def _manual_install_tesseract() -> None:
    subprocess.run(['apt download tesseract-ocr'],
        shell=True)
    proc = subprocess.run(['ls *.deb'],
        shell=True, capture_output=True)
    filename = proc.stdout.decode().strip()
    subprocess.run([f'dpkg -x {filename} {VENV_PATH}'],
        shell=True)
    subprocess.run(['rm *.deb'],
        shell=True)

    proc = subprocess.run([f'cd {VENV_PATH}/usr/bin; pwd'],
        shell=True, executable='/bin/bash', capture_output=True)
    path = proc.stdout.decode().strip()
    print('PATH =', path)
    subprocess.run([f'export PATH=\'$PATH:{path}\''],
        shell=True)
    subprocess.run(['source ~/.profile'],
        shell=True, executable='/bin/bash')
    
    print(ansi.ansi('Tesseract installed!').yellow())
    return

def _install_venv() -> None:
    print(ansi.ansi('installing python3-venv').yellow())
    proc = subprocess.Popen(['sudo apt-get -y install python3-venv'],
        shell=True)
    proc.wait()

    print(ansi.ansi('creating virtual environment').yellow())
    proc = subprocess.Popen([f'python3 -m venv {VENV_PATH}'],
        shell=True)
    proc.wait()
    return

def _install_pip_packages() -> None:
    print(ansi.ansi('installing pip packages').yellow())
    proc = subprocess.Popen([f'source {VENV_PATH}/bin/activate; pip3 install opencv-python pytesseract requests discord psutil; deactivate'],
        executable='/bin/bash', shell=True)
    proc.wait()
    return

# install/setup flow:
# 1.)   Make sure `python3-venv` is installed.
#       - For Python versions older than 3.4, `virtualenv` in also required.
# 2.)   Create the virtual environment in directory `VENV_PATH`.
#       - For Python versions older than 3.4, this can be created with the
#           following command: 'virtualenv <path>'.
# 3.)   Install all required pip packages whose names are in `PIP_PACKAGE_NAMES`.
# 4.)   Download and manually install `tesseract-ocr`.
def install() -> None:
    _install_venv()
    _install_pip_packages()
    _manual_install_tesseract()
    print(ansi.ansi('Successfully installed!').green())
    return

def uninstall() -> None:
    _remove_apt_packages()
    print(ansi.ansi('Successfully uninstalled!').green())
    return

def main() -> None:
    char = input('(1) Install\n(2) Uninstall\n> ')[0]
    if char == '1':     install()
    elif char == '2':   uninstall()
    else:               quit('invalid option')

    print(ansi.ansi('my_setup.py ').italic() + ansi.ansi('DONE').yellow())
    return

main()



"""
'The following additional packages will be installed:'
    fontconfig
    libcairo2
    libdatrie1
    libgif7
    libgraphite2-3
    libharfbuzz0b
    libjbig0
    libjpeg-turbo8
    libjpeg8
    liblept5
    libopenjp2-7
    libpango-1.0-0
    libpangocairo-1.0-0
    libpangoft2-1.0-0
    libpixman-1-0
    libtesseract4
    libthai-data
    libthai0
    libtiff5
    libwebp6
    libwebpmux3
    libxcb-render0
    --------------------------
    --------------------------
    tesseract-ocr-eng
    tesseract-ocr-osd

'The following NEW packages will be installed:'
    fontconfig                      Removing fontconfig (2.13.1-2ubuntu3) ...
    libcairo2                       Removing libcairo2:amd64 (1.16.0-4ubuntu1) ...
    libdatrie1                      Removing libdatrie1:amd64 (0.2.12-3) ...
    libgif7                         Removing libgif7:amd64 (5.1.9-1) ...
    libgraphite2-3                  Removing libgraphite2-3:amd64 (1.3.13-11build1) ...
    libharfbuzz0b                   Removing libharfbuzz0b:amd64 (2.6.4-1ubuntu4) ...
    libjbig0                        Removing libjbig0:amd64 (2.1-3.1build1) ...
    libjpeg-turbo8                  Removing libjpeg-turbo8:amd64 (2.0.3-0ubuntu1.20.04.1) ...
    libjpeg8                        Removing libjpeg8:amd64 (8c-2ubuntu8) ...
    liblept5                        Removing liblept5:amd64 (1.79.0-1) ...
    libopenjp2-7                    Removing libopenjp2-7:amd64 (2.3.1-1ubuntu4.20.04.1) ...
    libpango-1.0-0                  Removing libpango-1.0-0:amd64 (1.44.7-2ubuntu4) ...
    libpangocairo-1.0-0             Removing libpangocairo-1.0-0:amd64 (1.44.7-2ubuntu4) ...
    libpangoft2-1.0-0               Removing libpangoft2-1.0-0:amd64 (1.44.7-2ubuntu4) ...
    libpixman-1-0                   Removing libpixman-1-0:amd64 (0.38.4-0ubuntu1) ...
    libtesseract4                   Removing libtesseract4:amd64 (4.1.1-2build2) ...
    libthai-data                    Removing libthai-data (0.1.28-3) ...
    libthai0                        Removing libthai0:amd64 (0.1.28-3) ...
    libtiff5                        Removing libtiff5:amd64 (4.1.0+git191117-2ubuntu0.20.04.3) ...
    libwebp6                        Removing libwebp6:amd64 (0.6.1-2ubuntu0.20.04.1) ...
    libwebpmux3                     Removing libwebpmux3:amd64 (0.6.1-2ubuntu0.20.04.1) ...
    libxcb-render0                  Removing libxcb-render0:amd64 (1.14-2) ...
    --------------------------
    python3-venv                    Removing python3-venv (3.8.2-0ubuntu2) ...
    tesseract-ocr                   Removing tesseract-ocr (4.1.1-2build2) ...
    --------------------------
    tesseract-ocr-eng               Removing tesseract-ocr-eng (1:4.00~git30-7274cfa-1) ...
    tesseract-ocr-osd               Removing tesseract-ocr-osd (1:4.00~git30-7274cfa-1) ...
"""

# # 'The following additional packages will be installed:\n'\
# # data = 'fontconfig libcairo2 libdatrie1 libgif7 libgraphite2-3 libharfbuzz0b\n'\
# #     '  libjbig0 libjpeg-turbo8 libjpeg8 liblept5 libopenjp2-7 libpango-1.0-0\n'\
# #     '  libpangocairo-1.0-0 libpangoft2-1.0-0 libpixman-1-0 libtesseract4\n'\
# #     '  libthai-data libthai0 libtiff5 libwebp6 libwebpmux3 libxcb-render0\n'\
# #     '  python3-venv tesseract-ocr tesseract-ocr-eng tesseract-ocr-osd\n'
# remove_apt_packages()
# raw_out = install_apt_packages()
# regex = re.compile(r'The following NEW packages will be installed:\n(.*)\n\d', re.DOTALL)
# str_val = regex.findall(raw_out)
# print(str_val)