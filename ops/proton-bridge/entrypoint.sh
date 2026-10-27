#!/bin/sh









set -e

export HOME="${HOME:-/root}"
mkdir -p "$HOME/.gnupg" "$HOME/.password-store"
chmod 700 "$HOME/.gnupg"



if [ ! -s "$HOME/.password-store/.gpg-id" ]; then
    echo "[bridge] Kulcstár inicializálása (GPG + pass). Ez egyszeri, néhány másodperc..."
    gpg --batch --generate-key /gpg-key-params
    pass init "bridge@myra-project.hu"
    echo "[bridge] Kulcstár kész."
fi

case "${1:-run}" in
    init|cli|--cli)


        exec protonmail-bridge --cli
        ;;
    run|--noninteractive|"")
        socat TCP-LISTEN:25,fork,reuseaddr TCP:127.0.0.1:1025 &
        exec protonmail-bridge --noninteractive
        ;;
    *)
        exec "$@"
        ;;
esac
