#!/bin/bash
# OS Detection Script
# Detects Linux distribution (Fedora/Debian) or reports unsupported
# Sets OS_TYPE variable for downstream scripts

if [ -f /etc/os-release ]; then
    # shellcheck source=/etc/os-release
    . /etc/os-release
    
    case "$ID" in
        fedora)
            export OS_TYPE="fedora"
            printf '\033[1;32mFedora detected\033[0m\n'
            return
            ;;
        debian|ubuntu)
            export OS_TYPE="debian"
            printf '\033[1;32mDebian detected\033[0m\n'
            return
            ;;
        *)
            export OS_TYPE="unsupported"
            printf '\033[1;31mDistro not supported. Create a bug at:\033[0m\n'
            printf '\033[1;36mhttps://github.com/piraz/ai_cli_sandboxed/issues\033[0m\n'
            exit 1
            ;;
    esac
else
    export OS_TYPE="unsupported"
    printf '\033[1;31mDistro not supported. Create a bug at:\033[0m\n'
    printf '\033[1;36mhttps://github.com/piraz/ai_cli_sandboxed/issues\033[0m\n'
    exit 1
fi
