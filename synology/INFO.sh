#!/bin/sh
# Copyright (c) 2019-2021 David Cavallini

. /pkgscripts-ng/include/pkg_util.sh

package="shadowsocks-libev"
version="3.3.5-1"
os_min_ver="7.0-40000"
displayname="Shadowsocks-libev"
arch="$(pkg_get_platform_family)"
maintainer="David Cavallini"
distributor="davidcava"
distributor_url="https://github.com/davidcava/"
support_url="https://github.com/davidcava/shadowsocks-libev-dsm/wiki"
description="Shadowsocks-libev package for Synology DSM7, with v2ray plugin included (and also the deprecated simple-obfs)."
description_fre="Paquet Shadowsocks-libev pour Synology DSM7, incluant le plugin v2ray-plugin (et aussi l'ancien simple-obfs)."
startable="yes"
ctl_stop="yes"
silent_install="yes"
silent_upgrade="yes"
silent_uninstall="yes"
precheckstartstop="no"
dsmuidir="ui"
dsmappname=SYNO.SDS.Shadowsockslibev.Application

[ "$(caller)" != "0 NULL" ] && return 0

pkg_dump_info
