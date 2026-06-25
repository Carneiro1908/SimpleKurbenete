import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import database

PORT = 8000
PUBLIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")

class FinanceAPIRequestHandler(BaseHTTPRequestHandler):
    
    # Mapeamento de tipos MIME para arquivos estáticos
    MIME_TYPES = {
        '.html': 'text/html; charset=utf-8',
        '.css': 'text/css; charset=utf-8',
        '.js': 'application/javascript; charset=utf-8',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.svg': 'image/svg+xml',
        '.ico': 'image/x-icon',
        '.json': 'application/json; charset=utf-8'
    }

    def send_json(self, data, status=200):
        """Envia resposta JSON com cabeçalhos CORS habilitados."""
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_OPTIONS(self):
        """Responde às requisições preflight do CORS."""
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Rotas da API REST
        if path == '/api/transactions':
            search = query.get('search', [''])[0]
            filter_type = query.get('type', ['all'])[0]
            filter_category = query.get('category', ['all'])[0]
            
            transactions = database.get_transactions(search, filter_type, filter_category)
            self.send_json(transactions)
            return

        elif path == '/api/stats':
            stats = database.get_stats()
            self.send_json(stats)
            return

        elif path == '/api/goals':
            goals = database.get_goals()
            self.send_json(goals)
            return

        # Servir Arquivos Estáticos
        if path == '/':
            path = '/index.html'

        # Resolver caminho real no diretório public
        filepath = os.path.join(PUBLIC_DIR, path.lstrip('/'))
        
        # Evitar ataques de Directory Traversal
        real_public_dir = os.path.realpath(PUBLIC_DIR)
        real_filepath = os.path.realpath(filepath)
        
        if not real_filepath.startswith(real_public_dir) or not os.path.exists(real_filepath) or os.path.isdir(real_filepath):
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"404 Not Found")
            return

        # Encontrar tipo MIME correto
        _, ext = os.path.splitext(real_filepath)
        content_type = self.MIME_TYPES.get(ext.lower(), 'application/octet-stream')

        # Servir o arquivo estático
        self.send_response(200)
        self.send_header('Content-Type', content_type)
        self.end_headers()
        with open(real_filepath, 'rb') as f:
            self.wfile.write(f.read())

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Obter tamanho do corpo e ler dados do POST
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8'))
        except json.JSONDecodeError:
            self.send_json({"error": "Formato JSON inválido"}, 400)
            return

        # Adicionar nova transação
        if path == '/api/transactions':
            description = body.get('description')
            amount = body.get('amount')
            trans_type = body.get('type')
            category = body.get('category')
            date_str = body.get('date')

            if not description or amount is None or not trans_type or not category:
                self.send_json({"error": "Campos obrigatórios ausentes"}, 400)
                return

            try:
                amount_float = float(amount)
            except ValueError:
                self.send_json({"error": "O valor (amount) deve ser um número válido"}, 400)
                return

            if trans_type not in ['income', 'expense']:
                self.send_json({"error": "Tipo inválido. Deve ser 'income' ou 'expense'"}, 400)
                return

            new_id = database.add_transaction(description, amount_float, trans_type, category, date_str)
            self.send_json({"success": True, "id": new_id}, 201)
            return

        # Atualizar meta de economia
        elif path == '/api/goals':
            target_amount = body.get('target_amount')
            saved_amount = body.get('saved_amount')

            if target_amount is None or saved_amount is None:
                self.send_json({"error": "Campos obrigatórios (target_amount, saved_amount) ausentes"}, 400)
                return

            try:
                target_float = float(target_amount)
                saved_float = float(saved_amount)
            except ValueError:
                self.send_json({"error": "Os valores devem ser numéricos"}, 400)
                return

            database.update_goal(target_float, saved_float)
            self.send_json({"success": True})
            return

        else:
            self.send_json({"error": "Rota não encontrada"}, 404)

    def do_DELETE(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path
        query = urllib.parse.parse_qs(parsed_url.query)

        # Deletar transação pelo ID
        if path == '/api/transactions':
            trans_id = query.get('id', [None])[0]
            if not trans_id:
                self.send_json({"error": "Parâmetro 'id' ausente na URL"}, 400)
                return

            try:
                trans_id = int(trans_id)
            except ValueError:
                self.send_json({"error": "O ID deve ser um número inteiro"}, 400)
                return

            success = database.delete_transaction(trans_id)
            if success:
                self.send_json({"success": True})
            else:
                self.send_json({"error": "Transação não encontrada ou já excluída"}, 404)
            return
        
        else:
            self.send_json({"error": "Rota não encontrada"}, 404)

def run():
    # Inicializar banco de dados
    print("Inicializando banco de dados SQLite...")
    database.init_db()
    
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, FinanceAPIRequestHandler)
    print(f"Servidor rodando com sucesso em http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nDesligando servidor...")
        httpd.server_close()

if __name__ == "__main__":
    run()
