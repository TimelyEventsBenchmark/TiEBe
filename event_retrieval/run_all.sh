#!/bin/bash

# Preparação igual ao seu script
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed."
    exit 1
fi

echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

[ ! -f requirements.txt ] && echo "Missing requirements.txt" && deactivate && exit 1
pip install -r requirements.txt

[ ! -f main.py ] && echo "Missing main.py" && deactivate && exit 1
[ ! -f years.txt ] && echo "Missing years.txt" && deactivate && exit 1
[ ! -f countries.txt ] && echo "Missing countries.txt" && deactivate && exit 1

mkdir -p output_events logs
rm -rf logs/*
# Gerar combinações e rodar em paralelo com até 4 processos
echo "Running in parallel..."
cat countries.txt | while read -r country; do
    mkdir -p "output_events/$country"
    cat years.txt | while read -r year; do
        echo "$country $year"
    done
done | xargs -n 2 -P 4 bash -c 'python3 main.py "$0" "$1" > logs/$0_$1.log 2>&1'

echo "Generating Statistics results into stats/results.json..."
python3 gen_statistics.py
python3 gen_statistics_from_linked.py

echo "Attention on those topics data ..."
python3 check_all_execs.py > pay_attention_topics.txt

# cat output_events/*/* | grep "link" | wc
# cat output_events/*/* | grep "\"Archieved\": \"2" | wc

deactivate
echo "Done!"
