
set -xe

pyside6-uic ./form.ui -o form.py
python main.py
