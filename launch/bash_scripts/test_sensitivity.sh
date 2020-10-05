#!/bin/sh

area='CH'
years='2020,2035,2050'
scenario='RCP26,RCP45,RCP85'
n_mc=1000


while getopts "d::f::c::g::y::s::" opt; do

  case $opt in

    d) directory_climada="$OPTARG"
    ;;
    f) directory_ch2018="$OPTARG"
    ;;
    c) n_mc="$OPTARG"
    ;;
    g) area="$OPTARG"
    ;;
    y) years="$OPTARG"
    ;;
    s) scenario="$OPTARG"
    ;;

  esac

done

path_model=$(pwd)

cd $directory_climada

source activate climada_env


cd $path_model


python3 ${path_model}/../python_scripts/test_sensitivity.py $directory_ch2018 $n_mc $area $years $scenario

#conda deactivate

echo 'script completed'
