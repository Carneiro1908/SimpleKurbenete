/**
 * Antigravity Finance - Core Frontend Logic
 * Integração com API REST, Manipulação do DOM e Gráficos SVG Dinâmicos
 */

const API_BASE = ''; // Usamos rotas relativas, já que o backend serve o frontend

// Elementos do DOM
const statusIndicator = document.getElementById('statusIndicator');
const statusText = document.getElementById('statusText');
const netBalanceEl = document.getElementById('netBalance');
const totalIncomeEl = document.getElementById('totalIncome');
const totalExpenseEl = document.getElementById('totalExpense');
const balanceTrendEl = document.getElementById('balanceTrend');

// Filtros e Busca
const searchInput = document.getElementById('searchInput');
const filterType = document.getElementById('filterType');
const filterCategory = document.getElementById('filterCategory');

// Tabela de Transações
const transactionsTableBody = document.getElementById('transactionsTableBody');

// Metas
const btnEditGoal = document.getElementById('btnEditGoal');
const btnCancelGoal = document.getElementById('btnCancelGoal');
const goalForm = document.getElementById('goalForm');
const goalProgressBar = document.getElementById('goalProgressBar');
const savedAmountText = document.getElementById('savedAmountText');
const targetAmountText = document.getElementById('targetAmountText');
const goalPercentText = document.getElementById('goalPercentText');
const inputTargetAmount = document.getElementById('inputTargetAmount');
const inputSavedAmount = document.getElementById('inputSavedAmount');

// Graficos SVG
const expenseDonutChart = document.getElementById('expenseDonutChart');
const chartLegend = document.getElementById('chartLegend');

// Modal
const btnOpenAddModal = document.getElementById('btnOpenAddModal');
const btnCloseModal = document.getElementById('btnCloseModal');
const btnCancelModal = document.getElementById('btnCancelModal');
const transactionModal = document.getElementById('transactionModal');
const transactionForm = document.getElementById('transactionForm');
const transDateInput = document.getElementById('transDate');

// Cores mapeadas para as categorias (Uso no Gráfico SVG)
const CATEGORY_COLORS = {
    'Alimentação': '#f59e0b',    // Amarelo/Laranja
    'Moradia': '#3b82f6',        // Azul
    'Entretenimento': '#ec4899', // Rosa
    'Transporte': '#14b8a6',     // Teal
    'Trabalho': '#10b981',       // Verde Emerald
    'Saúde': '#ef4444',          // Vermelho
    'Outros': '#8b5cf6'          // Violeta
};

// 1. Inicialização do App
document.addEventListener('DOMContentLoaded', () => {
    // Definir data padrão no input do modal para hoje
    const today = new Date().toISOString().split('T')[0];
    transDateInput.value = today;

    // Carregar dados iniciais
    loadDashboardData();

    // Configurar ouvintes de eventos
    setupEventListeners();
});

// 2. Ouvintes de Eventos (Event Listeners)
function setupEventListeners() {
    // Busca e Filtros
    searchInput.addEventListener('input', debounce(loadTransactions, 300));
    filterType.addEventListener('change', loadTransactions);
    filterCategory.addEventListener('change', loadTransactions);

    // Modal de Adição
    btnOpenAddModal.addEventListener('click', openModal);
    btnCloseModal.addEventListener('click', closeModal);
    btnCancelModal.addEventListener('click', closeModal);
    transactionModal.addEventListener('click', (e) => {
        if (e.target === transactionModal) closeModal();
    });
    
    // Submissão do Formulário de Transação
    transactionForm.addEventListener('submit', handleAddTransaction);

    // Meta de Economia
    btnEditGoal.addEventListener('click', toggleGoalForm);
    btnCancelGoal.addEventListener('click', toggleGoalForm);
    goalForm.addEventListener('submit', handleUpdateGoal);
}

// 3. Funções de Chamada de API e Atualização de Estado

async function loadDashboardData() {
    try {
        await Promise.all([
            loadStats(),
            loadTransactions(),
            loadGoal()
        ]);
        setAPIStatus(true, 'Conectado à API (SQLite)');
    } catch (error) {
        console.error('Erro de conexão com a API:', error);
        setAPIStatus(false, 'Desconectado do Servidor');
    }
}

function setAPIStatus(connected, message) {
    if (connected) {
        statusIndicator.className = 'status-indicator connected';
        statusText.textContent = message;
    } else {
        statusIndicator.className = 'status-indicator disconnected';
        statusText.textContent = message;
    }
}

// Carregar Estatísticas do Dashboard
async function loadStats() {
    const res = await fetch(`${API_BASE}/api/stats`);
    if (!res.ok) throw new Error('Falha ao buscar estatísticas');
    const stats = await res.json();

    // Atualizar saldos e totais
    animateValue(netBalanceEl, stats.net_balance, true);
    animateValue(totalIncomeEl, stats.total_income);
    animateValue(totalExpenseEl, stats.total_expense);

    // Tendência do Balanço
    if (stats.net_balance > 0) {
        balanceTrendEl.textContent = 'Saldo positivo. Bom trabalho!';
        balanceTrendEl.style.color = 'var(--color-income)';
    } else if (stats.net_balance < 0) {
        balanceTrendEl.textContent = 'Balanço negativo. Reduza gastos!';
        balanceTrendEl.style.color = 'var(--color-expense)';
    } else {
        balanceTrendEl.textContent = 'Balanço neutro.';
        balanceTrendEl.style.color = 'var(--text-muted)';
    }

    // Renderizar gráfico
    renderChart(stats.categories, stats.total_expense);
}

// Carregar Meta de Economia
async function loadGoal() {
    const res = await fetch(`${API_BASE}/api/goals`);
    if (!res.ok) throw new Error('Falha ao buscar metas');
    const goal = await res.json();

    const target = goal.target_amount || 0;
    const saved = goal.saved_amount || 0;
    
    // Atualizar inputs do formulário
    inputTargetAmount.value = target;
    inputSavedAmount.value = saved;

    // Atualizar textos e barra de progresso
    targetAmountText.textContent = formatCurrency(target);
    savedAmountText.textContent = formatCurrency(saved);
    
    let percent = 0;
    if (target > 0) {
        percent = Math.min(Math.round((saved / target) * 100), 100);
    }
    
    goalProgressBar.style.width = `${percent}%`;
    goalPercentText.textContent = `${percent}% atingido`;
}

// Carregar Transações Recentes
async function loadTransactions() {
    const search = searchInput.value;
    const type = filterType.value;
    const category = filterCategory.value;

    const url = new URL(`${API_BASE}/api/transactions`, window.location.origin);
    if (search) url.searchParams.append('search', search);
    if (type !== 'all') url.searchParams.append('type', type);
    if (category !== 'all') url.searchParams.append('category', category);

    const res = await fetch(url);
    if (!res.ok) throw new Error('Falha ao buscar transações');
    const transactions = await res.json();

    renderTransactionsTable(transactions);
}

// 4. Renderização do DOM

function renderTransactionsTable(transactions) {
    if (transactions.length === 0) {
        transactionsTableBody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center py-4 muted">Nenhuma transação encontrada.</td>
            </tr>
        `;
        return;
    }

    transactionsTableBody.innerHTML = transactions.map(t => {
        const valueClass = t.type === 'income' ? 'value-income' : 'value-expense';
        const sign = t.type === 'income' ? '+' : '-';
        const formattedDate = formatDate(t.date);
        
        return `
            <tr id="row-${t.id}">
                <td class="transaction-title-cell">${escapeHTML(t.description)}</td>
                <td><span class="badge-category">${escapeHTML(t.category)}</span></td>
                <td class="muted">${formattedDate}</td>
                <td class="${valueClass} text-right">${sign} ${formatCurrency(t.amount)}</td>
                <td class="text-center">
                    <div class="action-buttons">
                        <button class="delete-btn" onclick="deleteTransaction(${t.id})" title="Excluir Transação">🗑</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

// Desenhar Gráfico SVG e Legenda
function renderChart(categories, totalExpense) {
    // Limpar o gráfico donut anterior, mantendo a circunferência base
    const baseCircles = expenseDonutChart.querySelectorAll('.donut-hole, .donut-ring');
    expenseDonutChart.innerHTML = '';
    baseCircles.forEach(c => expenseDonutChart.appendChild(c));
    chartLegend.innerHTML = '';

    const categoriesList = Object.entries(categories);

    if (categoriesList.length === 0 || totalExpense === 0) {
        chartLegend.innerHTML = `<div class="no-chart-data">Nenhuma despesa para exibir.</div>`;
        return;
    }

    let accumulatedPercentage = 0;

    categoriesList.forEach(([category, value]) => {
        const percentage = (value / totalExpense) * 100;
        const color = CATEGORY_COLORS[category] || '#6b7280'; // Fallback cinza

        // Criar círculo SVG para o segmento
        // O raio 15.91549430918954 garante que o perímetro do círculo seja exatamente 100
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('class', 'donut-segment');
        circle.setAttribute('cx', '18');
        circle.setAttribute('cy', '18');
        circle.setAttribute('r', '15.91549430918954');
        circle.setAttribute('fill', 'transparent');
        circle.setAttribute('stroke', color);
        circle.setAttribute('stroke-width', '3');
        
        // stroke-dasharray="porcentagem do segmento (comprimento) e 100 (tamanho total)"
        circle.setAttribute('stroke-dasharray', `${percentage.toFixed(4)} ${(100 - percentage).toFixed(4)}`);
        
        // stroke-dashoffset = rotaciona o segmento para não sobrepor.
        // É negativo pois roda no sentido horário, acumulando o percentual das fatias anteriores
        circle.setAttribute('stroke-dashoffset', `${(-accumulatedPercentage).toFixed(4)}`);
        
        expenseDonutChart.appendChild(circle);

        accumulatedPercentage += percentage;

        // Criar item da legenda correspondente
        const legendItem = document.createElement('div');
        legendItem.className = 'legend-item';
        legendItem.innerHTML = `
            <span class="legend-color" style="background-color: ${color}"></span>
            <span>${escapeHTML(category)}</span>
            <span class="legend-value">${formatCurrency(value)}</span>
        `;
        chartLegend.appendChild(legendItem);
    });
}

// 5. Manipulação de Envio de Dados (Forms & Modals)

// Adicionar Transação
async function handleAddTransaction(e) {
    e.preventDefault();

    const payload = {
        description: document.getElementById('transDescription').value,
        amount: parseFloat(document.getElementById('transAmount').value),
        type: document.getElementById('transType').value,
        category: document.getElementById('transCategory').value,
        date: document.getElementById('transDate').value
    };

    try {
        const res = await fetch(`${API_BASE}/api/transactions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Erro ao adicionar transação');

        // Resetar formulário, fechar modal e recarregar dados do dashboard
        transactionForm.reset();
        transDateInput.value = new Date().toISOString().split('T')[0];
        closeModal();
        await loadDashboardData();
    } catch (error) {
        alert('Erro ao salvar transação. Tente novamente.');
        console.error(error);
    }
}

// Deletar Transação
async function deleteTransaction(id) {
    if (!confirm('Deseja realmente excluir esta transação?')) return;

    try {
        const res = await fetch(`${API_BASE}/api/transactions?id=${id}`, {
            method: 'DELETE'
        });

        if (!res.ok) throw new Error('Erro ao deletar transação');

        // Animação de fade-out antes de remover a linha da tabela
        const row = document.getElementById(`row-${id}`);
        if (row) {
            row.style.opacity = '0';
            row.style.transform = 'translateX(20px)';
            row.style.transition = 'all 0.3s ease';
            setTimeout(async () => {
                await loadDashboardData();
            }, 300);
        } else {
            await loadDashboardData();
        }
    } catch (error) {
        alert('Erro ao excluir transação.');
        console.error(error);
    }
}

// Atualizar Meta
async function handleUpdateGoal(e) {
    e.preventDefault();

    const payload = {
        target_amount: parseFloat(inputTargetAmount.value),
        saved_amount: parseFloat(inputSavedAmount.value)
    };

    try {
        const res = await fetch(`${API_BASE}/api/goals`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error('Erro ao atualizar meta');

        toggleGoalForm();
        await loadGoal();
    } catch (error) {
        alert('Erro ao atualizar meta.');
        console.error(error);
    }
}

// 6. Controle dos Modais e Formulários

function openModal() {
    transactionModal.classList.add('show');
}

function closeModal() {
    transactionModal.classList.remove('show');
}

function toggleGoalForm() {
    goalForm.classList.toggle('hidden');
}

// 7. Utilitários Globais

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL'
    }).format(value);
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    const [year, month, day] = dateStr.split('-');
    return `${day}/${month}/${year}`;
}

function escapeHTML(str) {
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

// Animação de subida de números (micro-interação premium)
function animateValue(obj, endValue, handleNegative = false) {
    let start = 0;
    const duration = 500; // ms
    const startTime = performance.now();
    
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Efeito EaseOutQuad
        const easeProgress = progress * (2 - progress);
        const currentValue = start + (endValue - start) * easeProgress;
        
        obj.textContent = formatCurrency(currentValue);
        
        // Cor especial se for saldo líquido negativo
        if (handleNegative) {
            if (endValue < 0) {
                obj.style.color = 'var(--color-expense)';
            } else {
                obj.style.color = 'var(--text-primary)';
            }
        }

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }
    
    requestAnimationFrame(update);
}

// Debounce utilitário para busca não sobrecarregar requisições
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
