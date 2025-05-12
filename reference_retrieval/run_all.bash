#!/bin/bash

countries=("Argentina" "Australia" "Brazil" "Canada" "China" "Colombia" "Ethiopia" "France" "Germany" "India" "Indonesia" "Mexico" "New_Zealand" "Nigeria" "Papua_New_Guinea" "Portugal" "Russia" "the_Democratic_Republic_of_the_Congo" "the_United_Kingdom" "the_United_States" "Turkey"  "Ukraine" "World")   
years=("2015" "2016" "2017" "2018" "2019" "2020" "2021" "2022" "2023" "2024" "2025")          

for country in "${countries[@]}"; do
    for year in "${years[@]}"; do
        echo "___________________________________________"
        echo "Processing country: $country, year: $year"
        python scrape.py "$country" "$year"
        echo "Finished processing $country - $year"
        echo "___________________________________________"
        echo
    done
done
