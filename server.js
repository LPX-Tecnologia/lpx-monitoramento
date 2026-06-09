

cat > server.js << 'EOF'
const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = 3000;
const FEEDBACK_FILE = path.join(__dirname, 'feedbacks.json');

// Carregar feedbacks existentes
let feedbacks = [];
if (fs.existsSync(FEEDBACK_FILE)) {
    feedbacks = JSON.parse(fs.readFileSync(FEEDBACK_FILE, 'utf8'));
}

const server = http.createServer((req, res) => {
    // CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

    if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
    }

    // Rota: GET /api/feedbacks
    if (req.method === 'GET' && req.url === '/api/feedbacks') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(feedbacks));
        return;
    }

    // Rota: POST /api/feedbacks
    if (req.method === 'POST' && req.url === '/api/feedbacks') {
        let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', () => {
            const feedback = JSON.parse(body);
            feedback.id = Date.now();
            feedback.date = new Date().toISOString();
            feedback.status = 'viewed';
            feedback.response = getAutoResponse(feedback.type);
            feedback.responseDate = new Date().toISOString();
            
            feedbacks.unshift(feedback);
            fs.writeFileSync(FEEDBACK_FILE, JSON.stringify(feedbacks, null, 2));
            
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ success: true, feedback }));
        });
        return;
    }

    // Servir arquivos estáticos
    let filePath = '.' + req.url;
    if (filePath === './') filePath = './index.html';

    const extname = path.extname(filePath);
    const contentTypes = {
        '.html': 'text/html',
        '.js': 'text/javascript',
        '.css': 'text/css',
        '.json': 'application/json',
        '.png': 'image/png',
        '.jpg': 'image/jpg',
    };

    fs.readFile(filePath, (error, content) => {
        if (error) {
            res.writeHead(404);
            res.end('Not found');
        } else {
            res.writeHead(200, { 'Content-Type': contentTypes[extname] || 'text/plain' });
            res.end(content, 'utf-8');
        }
    });
});

function getAutoResponse(type) {
    const responses = {
        bug: ['Bug em análise pela equipe! 🐛🔍', 'Correção em andamento!'],
        sugestao: ['Ótima sugestão! Vamos avaliar. 💡', 'Adicionado ao roadmap! 🗺️'],
        elogio: ['Muito obrigado! 😊❤️', 'Ficamos felizes! 🚀'],
        feature: ['Funcionalidade interessante! Vamos analisar. 🔍']
    };
    const arr = responses[type] || ['Obrigado pelo feedback! 💚'];
    return arr[Math.floor(Math.random() * arr.length)];
}

server.listen(PORT, () => {
    console.log(`✅ Servidor de Feedback rodando em http://localhost:${PORT}`);
});