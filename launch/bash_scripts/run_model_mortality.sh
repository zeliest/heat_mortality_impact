#!/bin/sh
 
years='2020,2035,2050'
scenario='RCP26,RCP45,RCP85'
save_matrix=0
n_mc=100

while getopts "d::f::c:::y::s::m::" opt; do

  case $opt in

    d) directory_climada="$OPTARG" 
    ;;
    f) directory_ch2018="$OPTARG"
    ;;
    c) n_mc="$OPTARG"
    ;;
    y) years="$OPTARG"
    ;;
    s) scenario="$OPTARG"
    ;;
    m) save_matrix="$OPTARG"
    ;;

  esac

done

path_model=$(pwd)

cd $directory_climada

source activate climada_env


cd $path_model


python3 ${path_model}/../python_scripts/model_run_mortality.py $directory_ch2018 $n_mc $years $scenario $save_matrix

#conda deactivate

echo 'script completed' 






