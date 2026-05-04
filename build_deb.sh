#!/usr/bin/env bash
# build_deb.sh — Build UClean .deb package
set -e

VERSION="1.0.0"
PKG="uclean_${VERSION}_all"
BUILD_DIR="deb-build/${PKG}"
DIST_DIR="dist"

echo "🔨 Building UClean v${VERSION} .deb..."

# Render icons from SVG first
echo "🎨 Rendering icons..."
python3 render_icons.py

# Clean previous build
rm -rf "${BUILD_DIR}"

# Create directory structure
mkdir -p "${BUILD_DIR}/DEBIAN"
mkdir -p "${BUILD_DIR}/usr/bin"
mkdir -p "${BUILD_DIR}/usr/share/uclean"
mkdir -p "${BUILD_DIR}/usr/share/applications"
mkdir -p "${BUILD_DIR}/usr/share/doc/uclean"
mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps"
for size in 16 22 24 32 48 64 128 256; do
  mkdir -p "${BUILD_DIR}/usr/share/icons/hicolor/${size}x${size}/apps"
done
mkdir -p "${DIST_DIR}"

# Copy files
cp uclean.py    "${BUILD_DIR}/usr/share/uclean/uclean.py"
cp uclean.svg   "${BUILD_DIR}/usr/share/icons/hicolor/scalable/apps/uclean.svg"

for size in 16 22 24 32 48 64 128 256; do
  cp "icons/${size}x${size}/apps/uclean.png" \
     "${BUILD_DIR}/usr/share/icons/hicolor/${size}x${size}/apps/uclean.png"
done

# Launcher script
cat > "${BUILD_DIR}/usr/bin/uclean" << 'EOF'
#!/usr/bin/env bash
exec python3 /usr/share/uclean/uclean.py "$@"
EOF

# Desktop entry
cat > "${BUILD_DIR}/usr/share/applications/uclean.desktop" << 'EOF'
[Desktop Entry]
Name=UClean
GenericName=System Cleaner
Comment=Bersihkan Ubuntu dengan satu klik
Exec=uclean
Icon=uclean
Terminal=false
Type=Application
Categories=System;Utility;
Keywords=clean;cleaner;junk;sampah;ubuntu;apt;
StartupNotify=true
EOF

# DEBIAN/control
cat > "${BUILD_DIR}/DEBIAN/control" << EOF
Package: uclean
Version: ${VERSION}
Architecture: all
Maintainer: Grizenzio Orchivillando <orchivillando@users.noreply.github.com>
Depends: python3, python3-gi, gir1.2-gtk-3.0, polkitd | policykit-1
Section: utils
Priority: optional
Homepage: https://github.com/orchivillando/uclean
Description: Ubuntu System Cleaner — Bersihkan Ubuntu dengan satu klik
 UClean adalah aplikasi GTK3 sederhana untuk membersihkan sampah sistem Ubuntu.
 Membersihkan APT cache, orphaned packages, journal logs, trash, thumbnails,
 dan versi snap lama hanya dengan satu klik.
EOF

# DEBIAN/postinst
cat > "${BUILD_DIR}/DEBIAN/postinst" << 'EOF'
#!/bin/bash
set -e
if [ -d "/home/$SUDO_USER/Desktop" ]; then
    cp /usr/share/applications/uclean.desktop "/home/$SUDO_USER/Desktop/uclean.desktop"
    chmod +x "/home/$SUDO_USER/Desktop/uclean.desktop"
    chown "$SUDO_USER:$SUDO_USER" "/home/$SUDO_USER/Desktop/uclean.desktop" 2>/dev/null || true
fi
update-desktop-database /usr/share/applications/ 2>/dev/null || true
gtk-update-icon-cache -f -t /usr/share/icons/hicolor/ 2>/dev/null || true
EOF

# DEBIAN/prerm
cat > "${BUILD_DIR}/DEBIAN/prerm" << 'EOF'
#!/bin/bash
set -e
for home_dir in /home/*/Desktop; do
    [ -f "$home_dir/uclean.desktop" ] && rm -f "$home_dir/uclean.desktop"
done
update-desktop-database /usr/share/applications/ 2>/dev/null || true
EOF

# Changelog
cat > "${BUILD_DIR}/usr/share/doc/uclean/changelog.Debian" << EOF
uclean (${VERSION}) stable; urgency=low

  * Initial release

 -- Grizenzio Orchivillando <orchivillando@users.noreply.github.com>  $(date -R)
EOF
gzip -9 "${BUILD_DIR}/usr/share/doc/uclean/changelog.Debian"

# Set permissions
chmod 755 "${BUILD_DIR}/DEBIAN/postinst"
chmod 755 "${BUILD_DIR}/DEBIAN/prerm"
chmod 755 "${BUILD_DIR}/usr/bin/uclean"
chmod 644 "${BUILD_DIR}/usr/share/uclean/uclean.py"
chmod 644 "${BUILD_DIR}/usr/share/applications/uclean.desktop"

# Build .deb
dpkg-deb --build --root-owner-group "${BUILD_DIR}" "${DIST_DIR}/uclean_${VERSION}_all.deb"

echo "✅ Done! Output: ${DIST_DIR}/uclean_${VERSION}_all.deb"
ls -lh "${DIST_DIR}/"
