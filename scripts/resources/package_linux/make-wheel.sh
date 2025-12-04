#!/bin/env bash

set -e

SKIP_DIRS_NAMED=(\
    'build' \
    'dist' \
    'venv' \
    '.venv' \
    '.github' \
    '.tox' \
    '.git' \
    '.idea' \
    'ci' \
    'conan' \
    'reports' \
    '.mypy_cache' \
    '__pycache__' \
    '.pytest_cache' \
    'uiucprescon.ocr.egg-info'\
    'wheelhouse'\
)

REMOVE_FILES_FIRST=(
  'CMakeUserPresets.json'
  )

WORKSPACE=/tmp/workspace
PYTHON_VERSIONS_TO_USE=("${@:2}")
SOURCE_PATH=$1

make_shadow_copy(){
  local source_path=$1
  local destination_path=$2
  echo 'Making a shadow copy to prevent modifying local files'
  prune_expr=()

  for name in "${SKIP_DIRS_NAMED[@]}"; do
      prune_expr+=(-name "$name" -type d -prune -o);
  done
  mkdir -p ${destination_path}

  (
    cd $source_path/ && \
    find . "${prune_expr[@]}" -type d -print | while read -r dir; do \
        mkdir -p "${destination_path}/$dir"
    done

    cd $source_path/ && \
    find . "${prune_expr[@]}" \( -type f -o -type l \) -print | while read -r file; do
        echo "$file"
        ln -sf "$source_path/$file" "${destination_path}/$file"
    done
  )

}

remove_offending_files(){
  local source_path=$1

  for f in "${REMOVE_FILES_FIRST[@]}"; do
      OFFENDING_FILE=${source_path}/$f
      if [ -f "$OFFENDING_FILE" ]; then
        echo "Removing copy from temporary working path to avoid issues: $OFFENDING_FILE";
        rm $OFFENDING_FILE;
      fi;
  done
}

remove_python_cache_files(){
  local source_path=$1
  echo 'Removing Python cache files'
  find ${source_path} -type d -name '__pycache__' -exec rm -rf {} +
  find ${source_path} -type f -name '*.pyc' -exec rm -f {} +
}

build_wheels(){
  local workspace=$1
  local out_path=$2
  local python_versions_to_use=("${@:3}")
  echo "using ${python_versions_to_use[@]}"
  for i in "${python_versions_to_use[@]}"; do
      echo "Creating wheel for Python version: $i";
      uv build --python=$i --python-preference=system --wheel --out-dir=$out_path "${workspace}";
      if [ $? -ne 0 ]; then
        echo "Failed to build wheel for Python $i";
        exit 1;
      fi;
  done
}

fix_wheels(){
  local source_path=$1
  local destination_path=$2
  echo 'Fixing up wheels'
  auditwheel -v repair $source_path/*.whl -w $destination_path/;
  for file in $destination_path/*manylinux*.whl; do
      auditwheel show $file
  done
}

make_shadow_copy "$SOURCE_PATH" "$WORKSPACE"
remove_offending_files "$WORKSPACE"
remove_python_cache_files "$WORKSPACE"
build_wheels "$WORKSPACE" /tmp/dist "${PYTHON_VERSIONS_TO_USE[@]}"
fix_wheels /tmp/dist /dist/

echo 'Done'
