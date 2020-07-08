REM py -3.6 -m nuitka -h

set CC=D:\work\mingw64\bin\gcc.exe

py -3.6 -m nuitka --show-progress --show-scons --plugin-enable=multiprocessing --nofollow-imports --follow-import-to=Script --output-dir=build main.py



pause