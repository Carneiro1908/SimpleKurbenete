import subprocess
import time
import urllib.request
import json
import os
import signal
import sys

SERVER_URL = "http://localhost:8000"

def run_tests():
    print("=== Iniciando Testes Automatizados da API REST ===")
    
    # 1. Iniciar o servidor HTTP do app em segundo plano
    server_process = subprocess.Popen(
        ["python3", "server.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid # Permite finalizar o processo de forma limpa no Linux
    )
    
    # Aguardar o servidor inicializar
    time.sleep(1.5)
    
    try:
        # Teste 1: Acessar a página principal (HTML estático)
        print("Teste 1: Acessando GET / ...", end=" ")
        req = urllib.request.Request(f"{SERVER_URL}/")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            html_content = res.read().decode('utf-8')
            assert "<title>Antigravity Finance" in html_content
            print("PASSOU ✅")

        # Teste 2: Buscar transações iniciais
        print("Teste 2: Acessando GET /api/transactions ...", end=" ")
        req = urllib.request.Request(f"{SERVER_URL}/api/transactions")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            transactions = json.loads(res.read().decode('utf-8'))
            assert isinstance(transactions, list)
            assert len(transactions) > 0
            print(f"PASSOU ✅ ({len(transactions)} transações encontradas)")

        # Teste 3: Adicionar nova transação via POST
        print("Teste 3: Acessando POST /api/transactions ...", end=" ")
        payload = {
            "description": "Café de Teste Automatizado",
            "amount": 8.50,
            "type": "expense",
            "category": "Alimentação",
            "date": "2026-06-25"
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            f"{SERVER_URL}/api/transactions",
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        new_transaction_id = None
        with urllib.request.urlopen(req) as res:
            assert res.status == 201
            resp_body = json.loads(res.read().decode('utf-8'))
            assert resp_body["success"] is True
            assert "id" in resp_body
            new_transaction_id = resp_body["id"]
            print(f"PASSOU ✅ (ID Criado: {new_transaction_id})")

        # Teste 4: Validar estatísticas calculadas via GET
        print("Teste 4: Acessando GET /api/stats ...", end=" ")
        req = urllib.request.Request(f"{SERVER_URL}/api/stats")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            stats = json.loads(res.read().decode('utf-8'))
            assert "total_income" in stats
            assert "total_expense" in stats
            assert "net_balance" in stats
            assert "categories" in stats
            assert "Alimentação" in stats["categories"]
            print("PASSOU ✅")

        # Teste 5: Excluir a transação criada via DELETE
        print(f"Teste 5: Acessando DELETE /api/transactions?id={new_transaction_id} ...", end=" ")
        req = urllib.request.Request(
            f"{SERVER_URL}/api/transactions?id={new_transaction_id}",
            method="DELETE"
        )
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            resp_body = json.loads(res.read().decode('utf-8'))
            assert resp_body["success"] is True
            print("PASSOU ✅")

        print("\n🎉 Todos os 5 testes automatizados da API passaram com sucesso! 🎉")
        
    except Exception as e:
        print(f"FALHOU ❌")
        print(f"Erro ocorrido: {e}")
        # Capturar logs do servidor em caso de falha
        stdout, stderr = server_process.communicate(timeout=1)
        if stderr:
            print("Logs de erro do servidor:")
            print(stderr.decode('utf-8'))
        sys.exit(1)
        
    finally:
        # Finalizar o processo do servidor de forma limpa
        print("Finalizando servidor de teste...")
        try:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
        except Exception:
            server_process.terminate()
            
if __name__ == "__main__":
    run_tests()
