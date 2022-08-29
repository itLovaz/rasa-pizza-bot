# rasa-pizza-bot
A [rasa](https://rasa.com/docs/rasa/2.x) assistant to order pizza developed as final project for the [Human Machine Dialogue](http://disi.unitn.it/~riccardi/page7/styled-3/page16.html) course @ [University of Trento](https://www.unitn.it/)

<br>

## Steps to run it
- Setup a virtual environment:
```shell
python3 -m venv ./venv
source ./venv/bin/activate
 -> set `include-system-site-packages` to `true` in venv/pyvenv.cfg
```
- Install the required packages:
```shell
pip3 install -U --user pip
pip3 install rasa==2.8.15
pip install --upgrade tensorflow
pip install absl-py==0.10
pip install ruamel.yaml==0.16.5
pip install tensorflow==2.6.5
```
- Train or run the assistant:
```shell
rasa train
rasa shell
```

<br>
