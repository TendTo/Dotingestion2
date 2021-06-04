from os import listdir
from os.path import isfile, join

pwd = '.'
output_filename = 'all.yaml'
onlyfiles = [join(pwd, f) for f in listdir(pwd) if (isfile(join(pwd, f)) and f.endswith(".yaml") and f != output_filename)]

configurations = []
for file in onlyfiles:
    with open(file, 'r', encoding='utf-8') as f:
        text = f.read()
        text = text if text[-1] == "\n" else text + "\n"
        configurations.append(text)

with open('all.yaml', 'w', encoding='utf-8') as f:
    text = "---\n".join(configurations)
    f.write(text)