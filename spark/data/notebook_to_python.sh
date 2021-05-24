if [ "$1" = "" ] || [ $# -lt 1 ]; then
    echo "Write the name of the name of the notebook file as the first argument"
elif [ "$2" = "" ] || [ $# -lt 2 ]; then
    echo "Write the name of the name of the python script as the second argument"
else
jq -j '
  .cells
  | map( select(.cell_type == "code") | .source + ["\n\n"] )
  | .[][]
  '   $1.ipynb > $2.py
fi