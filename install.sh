#!/bin/sh
#installation script for package xivo-recording

PF_XIVO_WEB_DEB_FILE="./pf-xivo-web-interface_12.21~20121024.134631.6cf6e1f-3_all.deb"
PY_SETUP="setup.py"
SQL_PATCH="xivo-recording-ddl.sql"

if [ ! -e $PF_XIVO_WEB_DEB_FILE ]; then
    echo "Web interface package (${PF_XIVO_WEB_DEB_FILE}) not found, exiting."
    exit 1
fi

if [ ! -e $PY_SETUP ]; then
    echo "Python setup file (${PY_SETUP}) not found, exiting."
    exit 1
fi

if [ ! -e $SQL_PATCH ]; then
    echo "SQL patch file (${SQL_PATCH}) not found, exiting."
    exit 1
fi

installDep() {
  echo "Installing dependencies..."
  apt-get install -y libevent-dev python-pip python-dev build-essential
  pip install gevent
  pip install tornado
  pip install flask
  pip install SQLAlchemy
  pip install xivo-client-sim
}

installPy() {
  echo "Running python installer..."
  python $PY_SETUP install
}

reloadAsterisk() {
  RECORDING_DIALPLAN="/etc/asterisk/extensions_extra.d/xivo-recording.conf"
  if [ ! -e $RECORDING_DIALPLAN ]; then
      echo "Xivo-recording dialplan configuration file (${RECORDING_DIALPLAN}) not found, exiting."
      exit 1
  fi
  chown asterisk:www-data ${RECORDING_DIALPLAN}
  chmod 660 ${RECORDING_DIALPLAN}
  echo "Reload Asterisk dialplan!"
  asterisk -x 'dialplan reload'
}

installDB() {
  echo "Modifying database..."
  cp $SQL_PATCH /tmp/xivo-recording-ddl.sql
  su - -c 'psql asterisk postgres -f /tmp/xivo-recording-ddl.sql' postgres

  rm /tmp/xivo-recording-ddl.sql
}

installWebI() {
  dpkg -i $PF_XIVO_WEB_DEB_FILE
  if [ $? -ne 0 ]; then
      echo "Installation of new package failed, restoring previous environment..."
      apt-get install pf-xivo-web-interface
      exit 1
  fi	

  echo "Creating web directory..."
  mkdir /var/lib/pf-xivo/sounds/campagnes
}

recordingAutostart() {
  echo "Parameter xivo-recording autostart"
  update-rc.d xivo-recording defaults
}

startRecording() {
  echo "Launching xivo-recording daemon..."
  /etc/init.d/xivo-recording status > /dev/null
  if [ $? -ne 0 ]; then
      /etc/init.d/xivo-recording start
  fi

  /etc/init.d/xivo-recording status
  if [ $? -ne 0 ]; then
      echo "Install failed!"
      exit 1
  else
      echo "Installation finished."
  fi
}

install() {
  installDep
  installPy
  reloadAsterisk
  installDB
  installWebI
  recordingAutostart
  startRecording
}


echo "Starting installation..."
echo "Are you sure you want to start XiVO-recording installation?"
echo "(service interruption possible, Asterisk dialplan reload, web interface upodate etc.)"
while true; do
    read -p "(y/n)" yn
    case $yn in
        [Yy]* ) install; break;;
        [Nn]* ) exit;;
        * ) echo "Please answer yes or no.";;
    esac
done

exit 0

