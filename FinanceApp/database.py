import sqlite3
import os
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "finance.db")

def get_db_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Cria as tabelas e insere dados iniciais fictícios se o banco estiver vazio."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Criar tabela de transações
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        amount REAL NOT NULL,
        type TEXT CHECK(type IN ('income', 'expense')) NOT NULL,
        category TEXT NOT NULL,
        date TEXT NOT NULL
    )
    """)
    
    # Criar tabela de metas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target_amount REAL NOT NULL,
        saved_amount REAL NOT NULL
    )
    """)
    
    conn.commit()
    
    # Verificar se já existem transações, caso contrário popular dados
    cursor.execute("SELECT COUNT(*) FROM transactions")
    if cursor.fetchone()[0] == 0:
        # Inserir transações fictícias nos últimos dias
        today = datetime.now()
        dummy_data = [
            ("Salário Mensal", 3500.00, "income", "Trabalho", (today - timedelta(days=5)).strftime("%Y-%m-%d")),
            ("Supermercado Semanal", 350.25, "expense", "Alimentação", (today - timedelta(days=4)).strftime("%Y-%m-%d")),
            ("Mensalidade Netflix", 55.90, "expense", "Entretenimento", (today - timedelta(days=3)).strftime("%Y-%m-%d")),
            ("Freelance UI Design", 1200.00, "income", "Trabalho", (today - timedelta(days=2)).strftime("%Y-%m-%d")),
            ("Abastecimento Carro", 180.00, "expense", "Transporte", (today - timedelta(days=2)).strftime("%Y-%m-%d")),
            ("Jantar Especial", 120.00, "expense", "Alimentação", (today - timedelta(days=1)).strftime("%Y-%m-%d")),
            ("Conta de Luz", 245.50, "expense", "Moradia", today.strftime("%Y-%m-%d"))
        ]
        cursor.executemany(
            "INSERT INTO transactions (description, amount, type, category, date) VALUES (?, ?, ?, ?, ?)",
            dummy_data
        )
        conn.commit()
        
    # Verificar se existe meta, caso contrário popular
    cursor.execute("SELECT COUNT(*) FROM goals")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO goals (target_amount, saved_amount) VALUES (?, ?)", (5000.00, 1500.00))
        conn.commit()
        
    conn.close()

def get_transactions(search="", filter_type="all", filter_category="all"):
    """Recupera transações aplicando busca e filtros opcionais."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM transactions WHERE 1=1"
    params = []
    
    if search:
        query += " AND description LIKE ?"
        params.append(f"%{search}%")
        
    if filter_type != "all":
        query += " AND type = ?"
        params.append(filter_type)
        
    if filter_category != "all":
        query += " AND category = ?"
        params.append(filter_category)
        
    query += " ORDER BY date DESC, id DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def add_transaction(description, amount, trans_type, category, date_str):
    """Adiciona uma nova transação."""
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO transactions (description, amount, type, category, date) VALUES (?, ?, ?, ?, ?)",
        (description, float(amount), trans_type, category, date_str)
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id

def delete_transaction(trans_id):
    """Exclui uma transação pelo ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    rows_affected = cursor.rowcount
    conn.close()
    return rows_affected > 0

def get_stats():
    """Calcula estatísticas para exibição no dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de Receitas
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'income'")
    total_income = cursor.fetchone()[0] or 0.0
    
    # Total de Despesas
    cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'expense'")
    total_expense = cursor.fetchone()[0] or 0.0
    
    # Despesas por Categoria
    cursor.execute("""
        SELECT category, SUM(amount) as value 
        FROM transactions 
        WHERE type = 'expense' 
        GROUP BY category
    """)
    category_rows = cursor.fetchall()
    categories = {row['category']: row['value'] for row in category_rows}
    
    # Balanço Líquido
    net_balance = total_income - total_expense
    
    conn.close()
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "net_balance": net_balance,
        "categories": categories
    }

def get_goals():
    """Recupera a meta de economia atual."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM goals ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return {"target_amount": 0.0, "saved_amount": 0.0}

def update_goal(target_amount, saved_amount):
    """Atualiza a meta de economia."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Como só temos um registro de metas, atualizamos o primeiro ou inserimos
    cursor.execute("SELECT id FROM goals ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        cursor.execute(
            "UPDATE goals SET target_amount = ?, saved_amount = ? WHERE id = ?",
            (float(target_amount), float(saved_amount), row['id'])
        )
    else:
        cursor.execute(
            "INSERT INTO goals (target_amount, saved_amount) VALUES (?, ?)",
            (float(target_amount), float(saved_amount))
        )
        
    conn.commit()
    conn.close()
    return True

if __name__ == "__main__":
    init_db()
    print("Banco de dados inicializado em:", DB_FILE)
