#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LPX - Sistema de Segurança e Monitoramento
Versão: 1.0.0
Autor: LPX Tecnologia
GitHub: github.com/seu-usuario/lpx-monitoramento
"""

import os
import sys
import cv2
import numpy as np
from datetime import datetime, timedelta
from flask import Flask, render_template_string, request, jsonify, Response, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import threading
import time
import webbrowser
import socket

# ============= CONFIGURAÇÃO =============
app = Flask(__name__)
app.config['SECRET_KEY'] = 'lpx_seguranca_2024_chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lpx_seguranca.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Criar pastas necessárias
os.makedirs('static', exist_ok=True)
os.makedirs('data', exist_ok=True)

# ============= MODELOS =============

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='operator')

class Camera(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    camera_id = db.Column(db.String(50), unique=True)
    location = db.Column(db.String(200))
    status = db.Column(db.String(20), default='inactive')

class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text)
    severity = db.Column(db.String(20))
    day_group = db.Column(db.String(10))
    week_group = db.Column(db.String(10))
    month_group = db.Column(db.String(7))
    year_group = db.Column(db.String(4))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============= CÂMERA VIRTUAL =============

class VirtualCamera:
    def __init__(self):
        self.frame = None
        self.running = False
        self.fps = 0
        self.detection_count = 0
        
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.update, daemon=True)
        self.thread.start()
        return True
    
    def update(self):
        frame_count = 0
        last_time = time.time()
        
        while self.running:
            # Criar frame virtual 640x480
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Fundo escuro com efeito gradiente
            for i in range(480):
                color = int(20 + (i/480) * 20)
                frame[i, :] = [color, color//2, color//3]
            
            # Borda decorativa
            cv2.rectangle(frame, (10, 10), (630, 470), (0, 255, 0), 2)
            
            # Título principal
            cv2.putText(frame, "LPX SEGURANCA", (140, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1.8, (0, 255, 0), 3)
            
            # Subtítulo
            cv2.putText(frame, "MONITORAMENTO INTELIGENTE", (100, 150), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            
            # Linha decorativa
            cv2.line(frame, (100, 170), (540, 170), (0, 255, 0), 2)
            
            # Informações do sistema
            cv2.putText(frame, "SISTEMA ATIVO 24h", (200, 210), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
            
            # Data e hora
            now = datetime.now()
            date_str = now.strftime("%d/%m/%Y")
            time_str = now.strftime("%H:%M:%S")
            
            cv2.putText(frame, f"Data: {date_str}", (150, 260), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
            cv2.putText(frame, f"Hora: {time_str}", (150, 300), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 1)
            
            # FPS
            cv2.putText(frame, f"FPS: {self.fps}", (20, 450), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
            
            # Status
            status_color = (0, 255, 0) if self.running else (0, 0, 255)
            cv2.circle(frame, (600, 30), 10, status_color, -1)
            cv2.putText(frame, "ONLINE", (540, 35), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 1)
            
            # Simular detecções aleatórias
            if frame_count % 50 == 0:
                self.simulate_detection(frame)
            
            self.frame = frame
            frame_count += 1
            
            # Calcular FPS
            current_time = time.time()
            if current_time - last_time >= 1.0:
                self.fps = frame_count
                frame_count = 0
                last_time = current_time
            
            time.sleep(0.03)
    
    def simulate_detection(self, frame):
        """Simula uma detecção visual"""
        x = np.random.randint(100, 500)
        y = np.random.randint(100, 350)
        cv2.rectangle(frame, (x, y), (x+80, y+100), (0, 255, 0), 2)
        cv2.putText(frame, "PESSOA", (x, y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        self.detection_count += 1
    
    def get_frame(self):
        if self.frame is not None:
            _, buffer = cv2.imencode('.jpg', self.frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return buffer.tobytes()
        return None
    
    def stop(self):
        self.running = False

# Instância global
camera = VirtualCamera()

# ============= ROTAS =============

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template_string(INDEX_HTML)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('index'))
        else:
            flash('❌ Usuário ou senha incorretos!')
    
    return render_template_string(LOGIN_HTML)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = camera.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.03)
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/add_camera', methods=['POST'])
def add_camera():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.json
    cam = Camera(
        name=data.get('name', 'Nova Câmera'),
        camera_id=f"CAM_{int(time.time())}",
        location=data.get('location', ''),
        status='active'
    )
    db.session.add(cam)
    db.session.commit()
    
    return jsonify({'success': True, 'camera_id': cam.camera_id})

@app.route('/api/cameras')
def get_cameras():
    if 'user_id' not in session:
        return jsonify([])
    
    cameras = Camera.query.all()
    return jsonify([{
        'id': c.id,
        'name': c.name,
        'camera_id': c.camera_id,
        'location': c.location,
        'status': 'active' if camera.running else 'inactive'
    } for c in cameras])

@app.route('/api/alerts')
def get_alerts():
    if 'user_id' not in session:
        return jsonify([])
    
    filter_type = request.args.get('filter', 'today')
    now = datetime.now()
    
    if filter_type == 'today':
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_type == 'week':
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    elif filter_type == 'month':
        start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
    
    alerts = Alert.query.filter(Alert.created_at >= start)\
                       .order_by(Alert.created_at.desc()).limit(100).all()
    
    return jsonify([{
        'id': a.id,
        'message': a.message,
        'severity': a.severity,
        'created_at': a.created_at.strftime('%d/%m/%Y %H:%M:%S'),
        'day': a.created_at.strftime('%d/%m/%Y')
    } for a in alerts])

@app.route('/api/create_alert', methods=['POST'])
def create_alert():
    if 'user_id' not in session:
        return jsonify({'error': 'Não autorizado'}), 401
    
    data = request.json
    now = datetime.now()
    
    alert = Alert(
        message=data.get('message', 'Alerta do sistema'),
        severity=data.get('severity', 'medium'),
        day_group=now.strftime('%Y-%m-%d'),
        week_group=now.strftime('%Y-W%W'),
        month_group=now.strftime('%Y-%m'),
        year_group=now.strftime('%Y')
    )
    db.session.add(alert)
    db.session.commit()
    
    return jsonify({'success': True, 'alert_id': alert.id})

@app.route('/api/statistics')
def get_statistics():
    if 'user_id' not in session:
        return jsonify({})
    
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    
    alerts_today = Alert.query.filter(Alert.created_at >= today_start).count()
    cameras_active = Camera.query.filter_by(status='active').count()
    
    return jsonify({
        'people_count': camera.detection_count,
        'vehicle_count': np.random.randint(0, 10),
        'face_count': np.random.randint(0, 5),
        'alert_count': alerts_today,
        'cameras_active': cameras_active if cameras_active > 0 else 1,
        'system_uptime': 'Ativo'
    })

# ============= TEMPLATES HTML =============

LOGIN_HTML = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LPX Segurança - Login</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 50%, #0a0a1a 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .login-container {
            background: rgba(20, 20, 40, 0.95);
            backdrop-filter: blur(20px);
            padding: 50px 40px;
            border-radius: 20px;
            border: 2px solid rgba(0, 255, 0, 0.2);
            box-shadow: 0 0 50px rgba(0, 255, 0, 0.1);
            width: 400px;
            text-align: center;
        }
        .logo-icon { font-size: 4em; margin-bottom: 10px; }
        .logo-text {
            color: #00ff00;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 5px;
            text-shadow: 0 0 30px rgba(0, 255, 0, 0.5);
        }
        .subtitle { color: #888; margin-bottom: 30px; }
        .input-group { margin-bottom: 20px; text-align: left; }
        .input-group label { color: #00ff00; margin-bottom: 8px; font-size: 0.9em; display: block; }
        .input-group input {
            width: 100%;
            padding: 15px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(0, 255, 0, 0.2);
            border-radius: 10px;
            color: white;
            font-size: 1em;
        }
        .input-group input:focus { outline: none; border-color: #00ff00; }
        .login-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(90deg, #009900, #00ff00);
            border: none;
            border-radius: 10px;
            color: black;
            font-size: 1.1em;
            font-weight: bold;
            cursor: pointer;
            margin-top: 10px;
        }
        .login-btn:hover { transform: translateY(-2px); }
        .error-message {
            color: #ff4444;
            margin: 15px 0;
            padding: 10px;
            background: rgba(255, 0, 0, 0.1);
            border-radius: 8px;
        }
        .demo-info {
            margin-top: 25px;
            padding: 15px;
            background: rgba(0, 255, 0, 0.05);
            border-radius: 10px;
            border: 1px dashed rgba(0, 255, 0, 0.3);
        }
        .demo-info p { color: #888; font-size: 0.85em; margin: 5px 0; }
        .demo-info strong { color: #00ff00; }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="logo-icon">🔒</div>
        <div class="logo-text">LPX</div>
        <div class="subtitle">Segurança e Monitoramento Inteligente</div>
        
        <form method="POST">
            <div class="input-group">
                <label>👤 Usuário</label>
                <input type="text" name="username" placeholder="Digite seu usuário" required>
            </div>
            <div class="input-group">
                <label>🔑 Senha</label>
                <input type="password" name="password" placeholder="Digite sua senha" required>
            </div>
            <button type="submit" class="login-btn">ACESSAR SISTEMA</button>
        </form>
        
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                <div class="error-message">{{ messages[0] }}</div>
            {% endif %}
        {% endwith %}
        
        <div class="demo-info">
            <p><strong>👤 Demo:</strong> admin</p>
            <p><strong>🔑 Senha:</strong> admin123</p>
        </div>
    </div>
</body>
</html>
'''

INDEX_HTML = '''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LPX - Sistema de Monitoramento</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a1a3a 100%);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: white;
            min-height: 100vh;
        }
        .header {
            background: rgba(0, 0, 0, 0.95);
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 3px solid #00ff00;
        }
        .header-left h1 { color: #00ff00; font-size: 1.8em; }
        .header-left span { color: #888; font-size: 0.9em; }
        .user-badge {
            background: rgba(0, 255, 0, 0.1);
            padding: 8px 15px;
            border-radius: 20px;
            border: 1px solid rgba(0, 255, 0, 0.3);
            color: #00ff00;
        }
        .logout-btn {
            padding: 8px 20px;
            background: rgba(255, 0, 0, 0.1);
            border: 1px solid #ff0000;
            color: #ff0000;
            border-radius: 5px;
            text-decoration: none;
        }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        .stat-card {
            background: rgba(255, 255, 255, 0.03);
            padding: 20px;
            border-radius: 15px;
            border: 1px solid rgba(0, 255, 0, 0.15);
            text-align: center;
        }
        .stat-icon { font-size: 2em; margin-bottom: 10px; }
        .stat-value { font-size: 2.2em; font-weight: bold; color: #00ff00; }
        .stat-label { color: #888; font-size: 0.85em; }
        .main-grid {
            display: grid;
            grid-template-columns: 1.5fr 1fr;
            gap: 20px;
        }
        .panel {
            background: rgba(255, 255, 255, 0.02);
            border-radius: 15px;
            padding: 20px;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .panel-title {
            color: #00ff00;
            font-size: 1.2em;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid rgba(0, 255, 0, 0.2);
        }
        .camera-feed {
            background: #000;
            border-radius: 10px;
            overflow: hidden;
            border: 2px solid rgba(0, 255, 0, 0.2);
            margin-bottom: 15px;
        }
        .camera-feed img { width: 100%; display: block; }
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
        }
        .btn-primary { background: #00ff00; color: black; }
        .btn-warning { background: #ffaa00; color: black; }
        .btn-danger { background: #ff4444; color: white; }
        .tabs { display: flex; gap: 8px; margin-bottom: 15px; }
        .tab {
            padding: 8px 16px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.15);
            color: #888;
            cursor: pointer;
            border-radius: 20px;
        }
        .tab.active { background: #00ff00; color: black; }
        .alert-item {
            background: rgba(255, 255, 255, 0.03);
            padding: 12px;
            margin: 8px 0;
            border-radius: 8px;
            border-left: 4px solid #00ff00;
        }
        .alert-high { border-left-color: #ff0000; }
        .alert-medium { border-left-color: #ffaa00; }
        .modal {
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.8);
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }
        .modal.show { display: flex; }
        .modal-content {
            background: #1a1a3a;
            padding: 30px;
            border-radius: 15px;
            width: 90%;
            max-width: 500px;
        }
        .form-group { margin-bottom: 15px; }
        .form-group label { color: #00ff00; display: block; margin-bottom: 5px; }
        .form-group input, .form-group select {
            width: 100%;
            padding: 10px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 8px;
            color: white;
        }
        @media (max-width: 768px) {
            .main-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-left">
            <h1>🔒 LPX SEGURANÇA E MONITORAMENTO</h1>
            <span>Sistema Inteligente de Vigilância</span>
        </div>
        <div style="display: flex; gap: 15px; align-items: center;">
            <div class="user-badge">👤 {{ session.get('username', 'Usuário') }}</div>
            <a href="/logout" class="logout-btn">🚪 Sair</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-icon">👥</div>
                <div class="stat-value" id="people-count">0</div>
                <div class="stat-label">Pessoas Detectadas</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🚗</div>
                <div class="stat-value" id="vehicle-count">0</div>
                <div class="stat-label">Veículos Registrados</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">👤</div>
                <div class="stat-value" id="face-count">0</div>
                <div class="stat-label">Rostos Reconhecidos</div>
            </div>
            <div class="stat-card">
                <div class="stat-icon">🚨</div>
                <div class="stat-value" id="alert-count">0</div>
                <div class="stat-label">Alertas Hoje</div>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="panel">
                <div class="panel-title">📹 Monitoramento em Tempo Real</div>
                <div class="camera-feed">
                    <img src="/video_feed" alt="Camera Feed">
                </div>
                <div>
                    <button class="btn btn-primary" onclick="showAddCameraModal()">+ Adicionar Câmera</button>
                    <button class="btn btn-warning" onclick="createAlert()">🔔 Gerar Alerta</button>
                    <button class="btn btn-warning" onclick="simulateDetection()">👤 Simular Detecção</button>
                </div>
            </div>
            
            <div class="panel">
                <div class="panel-title">🚨 Central de Alertas</div>
                <div class="tabs">
                    <button class="tab active" onclick="filterAlerts('today', this)">Hoje</button>
                    <button class="tab" onclick="filterAlerts('week', this)">Semana</button>
                    <button class="tab" onclick="filterAlerts('month', this)">Mês</button>
                    <button class="tab" onclick="filterAlerts('year', this)">Ano</button>
                </div>
                <div id="alerts-container" style="max-height: 500px; overflow-y: auto;">
                    <p style="text-align: center; color: #666;">📭 Nenhum alerta</p>
                </div>
            </div>
        </div>
    </div>
    
    <div class="modal" id="cameraModal">
        <div class="modal-content">
            <h2 style="color: #00ff00;">➕ Adicionar Nova Câmera</h2>
            <form id="addCameraForm">
                <div class="form-group">
                    <label>Nome da Câmera</label>
                    <input type="text" id="camName" required>
                </div>
                <div class="form-group">
                    <label>URL/IP</label>
                    <input type="text" id="camUrl">
                </div>
                <div class="form-group">
                    <label>Localização</label>
                    <input type="text" id="camLocation">
                </div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button type="button" class="btn btn-danger" onclick="closeModal()">Cancelar</button>
                    <button type="submit" class="btn btn-primary">Adicionar</button>
                </div>
            </form>
        </div>
    </div>
    
    <script>
        function showAddCameraModal() {
            document.getElementById('cameraModal').classList.add('show');
        }
        
        function closeModal() {
            document.getElementById('cameraModal').classList.remove('show');
        }
        
        function filterAlerts(period, button) {
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            button.classList.add('active');
            
            fetch(`/api/alerts?filter=${period}`)
                .then(r => r.json())
                .then(alerts => {
                    const container = document.getElementById('alerts-container');
                    if (!alerts || alerts.length === 0) {
                        container.innerHTML = '<p style="text-align: center; color: #666;">📭 Nenhum alerta</p>';
                    } else {
                        container.innerHTML = alerts.map(a => `
                            <div class="alert-item alert-${a.severity}">
                                <strong>${a.message}</strong>
                                <div style="font-size: 0.8em; color: #888; margin-top: 5px;">🕐 ${a.created_at}</div>
                            </div>
                        `).join('');
                    }
                });
        }
        
        function createAlert() {
            const messages = [
                '🚨 Movimento suspeito detectado',
                '👤 Pessoa não autorizada',
                '🚗 Veículo desconhecido',
                '⚠️ Objeto abandonado',
                '🔔 Porta acionada'
            ];
            
            fetch('/api/create_alert', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    message: messages[Math.floor(Math.random() * messages.length)],
                    severity: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)]
                })
            })
            .then(() => {
                filterAlerts('today', document.querySelector('.tab.active'));
                updateStats();
            });
        }
        
        function simulateDetection() {
            const peopleCount = document.getElementById('people-count');
            peopleCount.textContent = parseInt(peopleCount.textContent) + Math.floor(Math.random() * 3) + 1;
        }
        
        function updateStats() {
            fetch('/api/statistics')
                .then(r => r.json())
                .then(stats => {
                    document.getElementById('people-count').textContent = stats.people_count || 0;
                    document.getElementById('vehicle-count').textContent = stats.vehicle_count || 0;
                    document.getElementById('face-count').textContent = stats.face_count || 0;
                    document.getElementById('alert-count').textContent = stats.alert_count || 0;
                });
        }
        
        document.getElementById('addCameraForm').addEventListener('submit', function(e) {
            e.preventDefault();
            fetch('/api/add_camera', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    name: document.getElementById('camName').value,
                    url: document.getElementById('camUrl').value || '0',
                    location: document.getElementById('camLocation').value
                })
            })
            .then(r => r.json())
            .then(result => {
                if (result.success) {
                    closeModal();
                    alert('✅ Câmera adicionada!');
                }
            });
        });
        
        filterAlerts('today', document.querySelector('.tab.active'));
        updateStats();
        setInterval(updateStats, 10000);
    </script>
</body>
</html>
'''

# ============= INICIALIZAÇÃO =============

def init_db():
    with app.app_context():
        db.create_all()
        
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', password='admin123', role='admin')
            db.session.add(admin)
            
            cam = Camera(
                name='Câmera Principal',
                camera_id='CAM_001',
                location='Entrada Principal',
                status='active'
            )
            db.session.add(cam)
            db.session.commit()
            print("✅ Banco de dados inicializado!")

def find_free_port():
    """Encontra uma porta livre"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        return s.getsockname()[1]

# ============= MAIN =============

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🔒 LPX - SEGURANÇA E MONITORAMENTO INTELIGENTE")
    print("="*60)
    
    init_db()
    camera.start()
    
    port = 5000
    url = f"http://localhost:{port}"
    
    print(f"""
✅ Sistema iniciado com sucesso!
📱 Acesse: {url}
👤 Usuário: admin
🔑 Senha: admin123

🌐 Abrindo navegador automaticamente...
    """)
    
    # Abrir navegador automaticamente
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    
    app.run(host='0.0.0.0', port=port, debug=False)