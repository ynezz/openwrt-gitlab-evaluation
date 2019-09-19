#!/usr/bin/env bash

set -euo pipefail

MIRROR_REPOS=" \
	project/procd \
	openwrt/openwrt \
	project/firewall3 \
	project/uci \
	project/ubus \
	project/rpcd \
	project/netifd \
	buildbot \
"

log() {
	echo "[*] mirror_repo: " "$@"
}

update_repo() {
	local repo
	local repo_path="$1"
	repo=$(basename "$repo_path")

	log "updating $repo"

	pushd "$repo" > /dev/null
	git fetch origin
	git push target --all --force || true
	popd > /dev/null
}

init_repo() {
	local repo
	local repo_path="$1"
	repo=$(basename "$repo_path")
	local src='git://git.openwrt.org'

	[ -d "$repo" ] && return 1

	log "initializing $repo"

	git clone --mirror "${src}/${repo_path}.git" "$repo"
	pushd "$repo" > /dev/null
	#git remote add --mirror=fetch target "git@code.fe80.eu:openwrt/$repo.git"
	git remote add --mirror=fetch target "git@gitlab.com:openwrtorg/$repo.git"
	git push target --all
	popd > /dev/null

	return 0
}

main() {
	for repo in $MIRROR_REPOS; do
		init_repo "$repo" || update_repo "$repo"
	done
}

main 2>&1 | tee mirror_repo.log
