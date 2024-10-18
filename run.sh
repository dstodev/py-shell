#!/bin/bash
set -euo pipefail

script_dir="$(builtin cd -- "$(dirname "$0")" && pwd -P)"
venv_dir="${script_dir}/.venv"

py=(python3.13)
pip=("${py[@]}" -m pip)

if [ ! -d "${venv_dir}" ]; then
	printf 'Creating Python virtual environment "%s"... ' "${venv_dir}"
	"${py[@]}" -m venv "${venv_dir}"
	printf ' done!\n'
fi

# shellcheck disable=SC1091
source "${venv_dir}/bin/activate"

packages=(
	pip
)

"${pip[@]}" install --upgrade --quiet "${packages[@]}"

"${py[@]}" "${script_dir}/src/main.py" "$@"
