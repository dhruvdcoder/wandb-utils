#!/usr/bin/env bash

ignore_files=".git|node_modules|_templates|customize|README.md"

for input_file in `tree -I "${ignore_files}" -Ffai --noreport`
do
  if [ ! -d "${input_file}" ]; then
    echo "Processing file: ${input_file}"
    gomplate \
         -f "${input_file}" \
         -o "${input_file}" \
         --left-delim "<<[" \
         --right-delim "]>>" \
         -c custom=./customize.json
  fi
done

# make necessary directories
chmod +x make_directories.sh
sh ./make_directories.sh

# Clean up / implode
rm README.md
mv README_TEMPLATE.md README.md
mv github .github
rm customize.sh
rm make_directories.sh
