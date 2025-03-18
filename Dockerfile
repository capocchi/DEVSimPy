# Utiliser une base Ubuntu
FROM ubuntu:22.04

# Mettre à jour et installer les dépendances nécessaires
RUN apt-get update && apt-get install -y \
    xfce4 xfce4-goodies \
    x11vnc xvfb \
    python3 python3-pip python3-venv \
    supervisor wget curl git \
    && rm -rf /var/lib/apt/lists/*

# Installer noVNC
RUN mkdir -p /opt/novnc \
    && git clone https://github.com/novnc/noVNC.git /opt/novnc \
    && git clone https://github.com/novnc/websockify /opt/novnc/utils/websockify \
    && ln -s /opt/novnc/vnc.html /opt/novnc/index.html

# Installer TigerVNC
RUN apt-get update && apt-get install -y tigervnc-standalone-server

# Installer DEVSimPy
RUN python3 -m venv /opt/devsimpy-env \
    && /opt/devsimpy-env/bin/pip install --upgrade pip \
    && /opt/devsimpy-env/bin/pip install devsimpy wxpython

# Configurer un mot de passe VNC (par défaut "password")
RUN mkdir -p /root/.vnc \
    && echo "password" | vncpasswd -f > /root/.vnc/passwd \
    && chmod 600 /root/.vnc/passwd

# Configurer Supervisor pour gérer les services
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Exposer les ports VNC et noVNC
EXPOSE 5901 6080

# Lancer les services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
