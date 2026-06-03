// ══════════════════ UTILITÁRIOS ══════════════════

function toast(msg, type = 'success') {
  const container = document.getElementById('toast-container');
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${type === 'success' ? '✅' : '❌'}</span> ${msg}`;
  container.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function updateClock() {
  const el = document.getElementById('clock');
  if (!el) return;
  el.textContent = new Date().toLocaleTimeString('pt-BR', {
    hour: '2-digit', minute: '2-digit', second: '2-digit'
  });
}
setInterval(updateClock, 1000);
updateClock();

const dateEl = document.getElementById('date-display');
if (dateEl) {
  dateEl.textContent = new Date().toLocaleDateString('pt-BR', {
    weekday: 'long', day: '2-digit', month: 'long', year: 'numeric'
  });
}

// ══════════════════ NAVEGAÇÃO ══════════════════

function navigate(page) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const target = document.getElementById(`page-${page}`);
  if (target) target.classList.add('active');
  const navBtn = document.querySelector(`[data-page="${page}"]`);
  if (navBtn) navBtn.classList.add('active');
  loadPage(page);
}

function loadPage(page) {
  if (page === 'dashboard')    loadDashboard();
  if (page === 'emprestimos')  loadEmprestimos();
  if (page === 'equipamentos') loadEquipamentos();
  if (page === 'relatorios')   loadRelatorio();
  if (page === 'inventario')   loadInventario();
  if (page === 'manutencoes')  loadManutencoes();
  if (page === 'usuarios')     loadUsuarios();
}

// ══════════════════ DASHBOARD ══════════════════

async function loadDashboard() {
  try {
    const res = await fetch('/api/chamados/dashboard');
    const d   = await res.json();
    document.getElementById('stat-total').textContent      = d.total;
    document.getElementById('stat-ativos').textContent     = d.ativos;
    document.getElementById('stat-atrasados').textContent  = d.atrasados;
    document.getElementById('stat-devolvidos').textContent = d.devolvidos;
  } catch (e) { console.error('Erro dashboard:', e); }

  try {
    const res  = await fetch('/api/chamados');
    const lista = await res.json();
    const tbody = document.getElementById('dashboard-recent');
    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="8" class="loading-cell">
        <div class="empty-state"><div class="icon">📋</div>
        <h3>Nenhum chamado registrado</h3>
        <p>Clique em "Novo Empréstimo" para começar.</p>
        </div></td></tr>`;
      return;
    }
    tbody.innerHTML = lista.slice(0, 8).map(c => rowChamadoHTML(c)).join('');
  } catch (e) { console.error('Erro recentes:', e); }
}

// ══════════════════ EMPRÉSTIMOS / CHAMADOS ══════════════════

let filtroStatus      = '';
let filtroInstituicao = '';
let termoBusca        = '';

async function loadEmprestimos() {
  const tbody = document.getElementById('emp-tbody');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8" class="loading-cell"><span class="loading-spinner"></span></td></tr>`;

  let url = '/api/chamados?';
  if (filtroInstituicao) url += `instituicao=${filtroInstituicao}&`;

  try {
    const res  = await fetch(url);
    let lista  = await res.json();

    if (filtroStatus) lista = lista.filter(c => c.status === filtroStatus);

    if (termoBusca) {
      const t = termoBusca.toLowerCase();
      lista = lista.filter(c =>
        c.responsavel.toLowerCase().includes(t) ||
        c.local_uso.toLowerCase().includes(t)   ||
        c.itens.some(e =>
          e.equipamento.toLowerCase().includes(t) ||
          e.patrimonio.toLowerCase().includes(t)
        )
      );
    }

    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="8" class="loading-cell">
        <div class="empty-state"><div class="icon">📦</div>
        <h3>Nenhum chamado encontrado</h3>
        <p>Ajuste os filtros ou registre um novo chamado.</p>
        </div></td></tr>`;
      return;
    }
    tbody.innerHTML = lista.map(c => rowChamadoHTML(c)).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="8" style="color:var(--atrasado);padding:20px;text-align:center">Erro ao carregar dados.</td></tr>`;
  }
}

function rowChamadoHTML(c) {
  const statusBadge = {
    'ativo':     `<span class="badge badge-ativo">● Ativo</span>`,
    'em_atraso': `<span class="badge badge-atrasado badge-pulse">⚠ Em Atraso</span>`,
    'devolvido': `<span class="badge badge-devolvido">✓ Devolvido</span>`
  }[c.status] || '';

  const instBadge = c.instituicao === 'UniFECAF'
    ? `<span class="badge-fecaf-pill">${c.instituicao}</span>`
    : `<span class="badge-ser-pill">${c.instituicao}</span>`;

  const equipLista = c.itens.map(e => {
    const devBadge = e.status === 'devolvido'
      ? `<span style="color:var(--devolvido);font-size:11px">✓ devolvido</span>`
      : e.status === 'em_atraso'
        ? `<span style="color:var(--atrasado);font-size:11px">⚠ atraso</span>`
        : `<button class="btn btn-ghost btn-sm" style="padding:2px 8px;font-size:11px" onclick="devolverItem(${e.id})">↩ devolver</button>`;
    return `<div style="display:flex;align-items:center;justify-content:space-between;padding:4px 0;border-bottom:1px solid var(--border)">
      <div>
        <span style="font-size:13px;font-weight:500">${e.equipamento}</span><br>
        <span style="color:var(--text-muted);font-size:11px">${e.patrimonio}</span>
      </div>
      ${devBadge}
    </div>`;
  }).join('');

  const temNaoDevolvido = c.itens.some(e => e.status !== 'devolvido');
  const acoes = c.status !== 'devolvido'
    ? `${temNaoDevolvido ? `<button class="btn btn-success btn-sm" onclick="devolverTudoChamado(${c.id})">↩ <span class="btn-devolver-texto">Devolver tudo</span></button>` : ''}
       <button class="btn btn-ghost btn-sm" onclick="adicionarEquipamentoChamado(${c.id})">＋ <span class="btn-devolver-texto">Item</span></button>
       <button class="btn btn-danger btn-sm" onclick="deletarChamado(${c.id})">🗑</button>`
    : `<button class="btn btn-ghost btn-sm" onclick="deletarChamado(${c.id})">🗑</button>`;

  return `<tr>
    <td><div>${equipLista}</div></td>
    <td>${c.responsavel}<br><small style="color:var(--text-muted)">${c.email}</small></td>
    <td>${c.local_uso}</td>
    <td class="col-inst">${instBadge}</td>
    <td>${c.data_hora_entrega}</td>
    <td>${c.data_hora_devolucao_prevista}</td>
    <td>${statusBadge}<br><small style="color:var(--text-muted)">${c.itens_devolvidos}/${c.total_itens} devolvidos</small></td>
    <td><div style="display:flex;gap:6px;flex-wrap:wrap">${acoes}</div></td>
  </tr>`;
}

async function devolverItem(empId) {
  if (!confirm('Confirmar devolução deste equipamento?')) return;
  try {
    await fetch(`/api/emprestimos/${empId}/devolver`, { method: 'POST' });
    toast('Devolução registrada!');
    loadEmprestimos();
    loadDashboard();
  } catch { toast('Erro.', 'error'); }
}

async function devolverTudoChamado(id) {
  if (!confirm('Devolver todos os equipamentos deste chamado?')) return;
  try {
    await fetch(`/api/chamados/${id}/devolver_tudo`, { method: 'POST' });
    toast('Todos os equipamentos devolvidos!');
    loadEmprestimos();
    loadDashboard();
  } catch { toast('Erro.', 'error'); }
}

async function adicionarEquipamentoChamado(chamadoId) {
  document.getElementById('add-item-chamado-id').value = chamadoId;
  const wrapper = document.getElementById('add-item-equip-wrapper');
  wrapper.innerHTML = '';
  try {
    const res = await fetch('/api/equipamentos');
    window._equipsGlobal = await res.json();
  } catch (e) { console.error(e); }
  await carregarBuscaEquipamento('add-item-equip-wrapper', 'add-item-equip-id');
  document.getElementById('modal-add-item').classList.add('open');
}

function closeModalAddItem() {
  document.getElementById('modal-add-item').classList.remove('open');
}

async function confirmarAddItem() {
  const chamadoId = document.getElementById('add-item-chamado-id').value;
  const equipId   = document.getElementById('add-item-equip-id')?.value;
  if (!equipId) { toast('Selecione um equipamento.', 'error'); return; }
  try {
    const res = await fetch(`/api/chamados/${chamadoId}/adicionar_equipamento`, {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ equipamento_id: equipId })
    });
    const d = await res.json();
    if (d.success) {
      toast('Equipamento adicionado ao chamado!');
      closeModalAddItem();
      loadEmprestimos();
      loadDashboard();
    } else {
      toast('Erro: ' + d.error, 'error');
    }
  } catch { toast('Erro de conexão.', 'error'); }
}

async function deletarChamado(id) {
  if (!confirm('Excluir este chamado e todos seus itens?')) return;
  try {
    await fetch(`/api/chamados/${id}`, { method: 'DELETE' });
    toast('Chamado excluído.');
    loadEmprestimos();
    loadDashboard();
  } catch { toast('Erro.', 'error'); }
}

function setFiltroStatus(el, status) {
  filtroStatus = status;
  document.querySelectorAll('.filter-chips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadEmprestimos();
}

function setFiltroInstituicao(inst) {
  filtroInstituicao = inst;
  loadEmprestimos();
}

// ══════════════════ MODAL CHAMADO ══════════════════

let _equipamentosCache = [];

async function openModalEmprestimo() {
  preencherDataAtual();
  selecionarTurno('manha');
  document.getElementById('equipamentos-lista').innerHTML = '';
  try {
    const res = await fetch('/api/equipamentos');
    _equipamentosCache = await res.json();
  } catch (e) { console.error(e); }
  adicionarLinhaEquipamento();
  document.getElementById('modal-emp').classList.add('open');
}

function closeModalEmprestimo() {
  document.getElementById('modal-emp').classList.remove('open');
  document.getElementById('form-emp').reset();
  document.getElementById('equipamentos-lista').innerHTML = '';
}

function preencherDataAtual() {
  const now = new Date();
  const pad = n => String(n).padStart(2, '0');
  const dt  = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
  document.getElementById('f-entrega').value = dt;
}

function atualizarLocal() {
  const unidade    = document.getElementById('f-unidade').value;
  const especifico = document.getElementById('f-local-especifico')?.value || '';
  const local      = document.getElementById('f-local');
  if (unidade && especifico) {
    local.value = `${especifico} (${unidade})`;
  } else if (unidade) {
    local.value = unidade;
  } else {
    local.value = '';
  }
}

function selecionarTurno(turno) {
  document.querySelectorAll('.turno-pill').forEach(p => p.classList.remove('selected'));
  const pill = document.querySelector(`[data-turno="${turno}"]`);
  if (pill) pill.classList.add('selected');
  document.getElementById('f-turno').value = turno;
  const now  = new Date();
  const pad  = n => String(n).padStart(2, '0');
  const data = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}`;
  const horarios = { manha: `${data}T10:00`, noite: `${data}T22:00`, outro: '' };
  document.getElementById('f-devolucao').value = horarios[turno] || '';
}

async function adicionarLinhaEquipamento() {
  if (!_equipamentosCache.length) {
    try {
      const res = await fetch('/api/equipamentos');
      _equipamentosCache = await res.json();
    } catch (e) { console.error(e); }
  }

  const lista   = document.getElementById('equipamentos-lista');
  const index   = lista.children.length;
  const div     = document.createElement('div');
  div.className = 'equip-linha';
  div.style     = 'display:flex;align-items:center;gap:8px;margin-bottom:4px';
  div.innerHTML = `
    <div style="flex:1;position:relative">
      <input type="text" placeholder="🔍 Digite o nome ou patrimônio..."
        id="equip-busca-${index}" autocomplete="off"
        oninput="filtrarEquipLinha(${index})"
        onfocus="mostrarDropdownLinha(${index})"
        style="width:100%">
      <input type="hidden" id="equip-id-${index}">
      <div id="equip-dd-${index}" style="display:none;position:absolute;top:100%;left:0;right:0;
        background:var(--bg-card);border:1px solid var(--border-hover);
        border-radius:var(--radius-sm);max-height:160px;overflow-y:auto;
        z-index:999;box-shadow:var(--shadow);margin-top:4px"></div>
    </div>
    <button type="button" class="btn btn-danger btn-sm" onclick="removerLinhaEquipamento(this)">✕</button>
  `;
  lista.appendChild(div);

  const disponiveis = _equipamentosCache.filter(e => !e.emprestado);
  preencherDropdownLinha(index, disponiveis);

  document.addEventListener('click', function(e) {
    const dd    = document.getElementById(`equip-dd-${index}`);
    const input = document.getElementById(`equip-busca-${index}`);
    if (dd && input && !input.contains(e.target) && !dd.contains(e.target)) {
      dd.style.display = 'none';
    }
  });
}

function mostrarDropdownLinha(index) {
  const dd = document.getElementById(`equip-dd-${index}`);
  if (dd) dd.style.display = 'block';
}

function preencherDropdownLinha(index, lista) {
  const dd = document.getElementById(`equip-dd-${index}`);
  if (!dd) return;
  if (!lista.length) {
    dd.innerHTML = `<div style="padding:10px 16px;color:var(--text-muted);font-size:13px">Nenhum equipamento disponível</div>`;
    return;
  }
  dd.innerHTML = lista.map(e => `
    <div onclick="selecionarEquipLinha(${index}, ${e.id}, '${e.nome}', '${e.patrimonio}')"
      style="padding:10px 16px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--border)"
      onmouseover="this.style.background='var(--bg-card2)'"
      onmouseout="this.style.background='transparent'">
      <strong>${e.nome}</strong>
      <span style="color:var(--text-muted);margin-left:8px">${e.patrimonio}</span>
    </div>`).join('');
}

function filtrarEquipLinha(index) {
  const input = document.getElementById(`equip-busca-${index}`);
  const dd    = document.getElementById(`equip-dd-${index}`);
  if (dd) dd.style.display = 'block';
  document.getElementById(`equip-id-${index}`).value = '';
  const t = input.value.toLowerCase();
  const filtrado = _equipamentosCache.filter(e =>
    !e.emprestado &&
    (e.nome.toLowerCase().includes(t) || e.patrimonio.toLowerCase().includes(t))
  );
  preencherDropdownLinha(index, filtrado);
}

function selecionarEquipLinha(index, id, nome, patrimonio) {
  document.getElementById(`equip-id-${index}`).value     = id;
  document.getElementById(`equip-busca-${index}`).value  = `${nome} — ${patrimonio}`;
  document.getElementById(`equip-dd-${index}`).style.display = 'none';
}

function removerLinhaEquipamento(btn) {
  btn.parentElement.remove();
}

async function salvarEmprestimo(event) {
  event.preventDefault();
  const btn = document.getElementById('btn-salvar-emp');

  const linhas = document.querySelectorAll('#equipamentos-lista .equip-linha');
  const equipamentos_ids = [];
  for (let i = 0; i < linhas.length; i++) {
    const id = document.getElementById(`equip-id-${i}`)?.value;
    if (id) equipamentos_ids.push(id);
  }

  if (!equipamentos_ids.length) {
    toast('Selecione pelo menos um equipamento.', 'error');
    return;
  }

  btn.disabled = true;
  btn.innerHTML = '<span class="loading-spinner"></span> Salvando...';

  const payload = {
    responsavel:                  document.getElementById('f-responsavel').value,
    email:                        document.getElementById('f-email').value,
    local_uso:                    document.getElementById('f-local').value,
    instituicao:                  document.getElementById('f-instituicao').value,
    turno:                        document.getElementById('f-turno').value,
    data_hora_entrega:            document.getElementById('f-entrega').value,
    data_hora_devolucao_prevista: document.getElementById('f-devolucao').value,
    observacoes:                  document.getElementById('f-obs').value,
    equipamentos_ids:             equipamentos_ids
  };

  try {
    const res = await fetch('/api/chamados', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.success) {
      toast(`Chamado #${d.id} registrado com sucesso! 📋`);
      closeModalEmprestimo();
      loadEmprestimos();
      loadDashboard();
    } else {
      toast('Erro: ' + d.error, 'error');
    }
  } catch {
    toast('Erro de conexão.', 'error');
  } finally {
    btn.disabled = false;
    btn.textContent = 'Registrar Chamado';
  }
}

// ══════════════════ EQUIPAMENTOS ══════════════════

async function loadEquipamentos() {
  const tbody = document.getElementById('equip-tbody');
  if (!tbody) return;
  try {
    const res   = await fetch('/api/equipamentos/todos');
    const lista = await res.json();
    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="5" class="loading-cell">
        <div class="empty-state"><div class="icon">🖥️</div>
        <h3>Nenhum equipamento cadastrado</h3>
        <p>Adicione equipamentos ao acervo.</p>
        </div></td></tr>`;
      return;
    }
    tbody.innerHTML = lista.map(eq => `<tr>
      <td><strong>${eq.nome}</strong></td>
      <td><code style="background:var(--bg-card2);padding:2px 8px;border-radius:4px;font-size:12px">${eq.patrimonio}</code></td>
      <td>${eq.descricao || '—'}</td>
      <td><span class="badge ${eq.ativo ? 'badge-devolvido' : 'badge-atrasado'}">${eq.ativo ? '● Ativo' : '○ Inativo'}</span></td>
      <td style="display:flex;gap:6px">
        <button class="btn btn-ghost btn-sm" onclick="editarEquipamento(${eq.id}, '${eq.nome}', '${eq.patrimonio}', \`${eq.descricao || ''}\`)">✏️ Editar</button>
        <button class="btn btn-danger btn-sm" onclick="toggleEquipamento(${eq.id}, ${eq.ativo})">${eq.ativo ? '🗑 Desativar' : '♻️ Ativar'}</button>
      </td>
    </tr>`).join('');
  } catch {
    tbody.innerHTML = `<tr><td colspan="5" style="color:var(--atrasado);padding:20px;text-align:center">Erro ao carregar.</td></tr>`;
  }
}

function openModalEquipamento() {
  document.getElementById('equip-modal-id').value = '';
  document.getElementById('equip-modal-title').textContent = '🖥️ Novo Equipamento';
  document.getElementById('form-equip').reset();
  document.getElementById('modal-equip').classList.add('open');
}

function closeModalEquipamento() {
  document.getElementById('modal-equip').classList.remove('open');
  document.getElementById('form-equip').reset();
}

function editarEquipamento(id, nome, patrimonio, descricao) {
  document.getElementById('equip-modal-id').value          = id;
  document.getElementById('equip-modal-title').textContent = '✏️ Editar Equipamento';
  document.getElementById('eq-nome').value                 = nome;
  document.getElementById('eq-patrimonio').value           = patrimonio;
  document.getElementById('eq-descricao').value            = descricao;
  document.getElementById('modal-equip').classList.add('open');
}

async function salvarEquipamento(event) {
  event.preventDefault();
  const id      = document.getElementById('equip-modal-id').value;
  const payload = {
    nome:       document.getElementById('eq-nome').value,
    patrimonio: document.getElementById('eq-patrimonio').value,
    descricao:  document.getElementById('eq-descricao').value
  };
  try {
    let res;
    if (id) {
      res = await fetch(`/api/equipamentos/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/equipamentos', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    }
    const d = await res.json();
    if (d.success) {
      toast(id ? 'Equipamento atualizado!' : 'Equipamento cadastrado!');
      closeModalEquipamento();
      loadEquipamentos();
    } else {
      toast('Erro: ' + d.error, 'error');
    }
  } catch { toast('Erro de conexão.', 'error'); }
}

async function toggleEquipamento(id, ativo) {
  const msg = ativo ? 'Desativar este equipamento?' : 'Reativar este equipamento?';
  if (!confirm(msg)) return;
  try {
    await fetch(`/api/equipamentos/${id}`, {
      method: 'PUT', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ ativo: !ativo })
    });
    toast(ativo ? 'Equipamento desativado.' : 'Equipamento reativado!');
    loadEquipamentos();
  } catch { toast('Erro ao atualizar.', 'error'); }
}

// ══════════════════ RELATÓRIOS ══════════════════

async function loadRelatorio() {
  const mes = document.getElementById('rel-mes')?.value || new Date().getMonth() + 1;
  const ano = document.getElementById('rel-ano')?.value || new Date().getFullYear();
  try {
    const res = await fetch(`/api/relatorios/mensal?mes=${mes}&ano=${ano}`);
    const d   = await res.json();
    document.getElementById('rel-total').textContent      = d.total;
    document.getElementById('rel-devolvidos').textContent = d.devolvidos;
    document.getElementById('rel-nao-dev').textContent    = d.nao_devolvidos;
    document.getElementById('rel-atrasados').textContent  = d.atrasados;
    renderBarChart('chart-equip', d.por_equipamento);
    renderBarChart('chart-resp',  d.por_responsavel);
    renderInstChart(d.por_instituicao);
    const tbody = document.getElementById('rel-naodev-tbody');
    if (!d.nao_devolvidos_lista.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--devolvido);padding:24px">
        ✅ Todos os equipamentos foram devolvidos neste período!</td></tr>`;
    } else {
      tbody.innerHTML = d.nao_devolvidos_lista.map(e => `<tr>
        <td>${e.equipamento} <small style="color:var(--text-muted)">(${e.patrimonio})</small></td>
        <td>${e.responsavel}</td><td>${e.email}</td>
        <td>${e.data_hora_entrega}</td><td>${e.data_hora_devolucao_prevista}</td>
        <td><span class="badge badge-${e.status === 'em_atraso' ? 'atrasado badge-pulse' : 'ativo'}">
          ${e.status === 'em_atraso' ? '⚠ Em Atraso' : '● Ativo'}</span></td>
      </tr>`).join('');
    }
  } catch (err) { console.error('Erro relatório:', err); }
}

function renderBarChart(containerId, data) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]).slice(0, 8);
  const max     = Math.max(...entries.map(e => e[1]), 1);
  if (!entries.length) {
    container.innerHTML = `<p style="color:var(--text-muted);font-size:13px">Sem dados no período.</p>`;
    return;
  }
  container.innerHTML = entries.map(([label, count]) => `
    <div class="bar-row">
      <span class="bar-label" title="${label}">${label}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${(count/max)*100}%"></div></div>
      <span class="bar-count">${count}</span>
    </div>`).join('');
}

function renderInstChart(data) {
  const container = document.getElementById('chart-inst');
  if (!container) return;
  const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;
  container.innerHTML = Object.entries(data).map(([inst, count]) => {
    const pct   = Math.round((count / total) * 100);
    const color = inst === 'UniFECAF' ? 'var(--fecaf-primary)' : 'var(--ser-primary)';
    return `<div class="bar-row">
      <span class="bar-label">${inst}</span>
      <div class="bar-track"><div class="bar-fill" style="width:${pct}%;background:${color}"></div></div>
      <span class="bar-count">${count}</span>
    </div>`;
  }).join('');
}

// ══════════════════ INVENTÁRIO ══════════════════

let filtroInvTipo     = '';
let filtroInvAlerta   = false;
let filtroInvGarantia = false;

async function loadInventario() {
  const tbody    = document.getElementById('inv-tbody');
  const categoria = document.getElementById('filtro-categoria')?.value || '';
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="8" class="loading-cell"><span class="loading-spinner"></span></td></tr>`;
  try {
    const resR = await fetch('/api/inventario/resumo');
    const resumo = await resR.json();
    document.getElementById('inv-total').textContent       = resumo.total;
    document.getElementById('inv-emprestavel').textContent = resumo.emprestavel;
    document.getElementById('inv-fixo').textContent        = resumo.fixo;
    document.getElementById('inv-baixo').textContent       = resumo.estoque_baixo;
    await carregarCategoriasSelect();
    let url = '/api/inventario?';
    if (filtroInvTipo)     url += `tipo=${filtroInvTipo}&`;
    if (filtroInvAlerta)   url += `alerta=true&`;
    if (filtroInvGarantia) url += `garantia=vencendo&`;
    if (categoria)         url += `categoria_id=${categoria}&`;
    const res  = await fetch(url);
    const lista = await res.json();
    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="8" class="loading-cell">
        <div class="empty-state"><div class="icon">📦</div>
        <h3>Nenhum item encontrado</h3><p>Ajuste os filtros ou cadastre um novo item.</p>
        </div></td></tr>`;
    } else {
      tbody.innerHTML = lista.map(e => rowInvHTML(e)).join('');
    }
    loadMovimentacoes();
  } catch (err) { console.error('Erro inventário:', err); }
}

function rowInvHTML(e) {
  const garantiaBadge = {
    'valida':       `<span class="badge badge-devolvido">✓ Válida</span>`,
    'vencendo':     `<span class="badge badge-atrasado badge-pulse">⚠ Vencendo</span>`,
    'vencida':      `<span class="badge badge-atrasado">✕ Vencida</span>`,
    'sem_garantia': `<span style="color:var(--text-dim);font-size:12px">—</span>`
  }[e.garantia_status] || '—';

  const tipoBadge = {
    'emprestavel': `<span class="badge badge-ativo">🔄 Emprestável</span>`,
    'fixo':        `<span class="badge badge-devolvido">📌 Fixo</span>`,
    'suprimento':  `<span class="badge" style="background:rgba(244,121,32,0.15);color:#F47920;border:1px solid rgba(244,121,32,0.3)">🔋 Suprimento</span>`
  }[e.tipo] || '';

  const qtdStyle = e.estoque_baixo ? `style="color:var(--atrasado);font-weight:700"` : '';

  return `<tr>
    <td><strong>${e.categoria_icone} ${e.nome}</strong>
      ${e.descricao && e.descricao !== '—' ? `<br><small style="color:var(--text-muted)">${e.descricao}</small>` : ''}
    </td>
    <td>${e.categoria}</td>
    <td>${tipoBadge}</td>
    <td><code style="background:var(--bg-card2);padding:2px 8px;border-radius:4px;font-size:12px">${e.patrimonio}</code></td>
    <td ${qtdStyle}>${e.quantidade} ${e.estoque_baixo ? '⚠' : ''}</td>
    <td>${e.localizacao}</td>
    <td>${garantiaBadge}${e.garantia_ate ? `<br><small style="color:var(--text-muted)">${e.garantia_ate}</small>` : ''}</td>
    <td>
      <div style="display:flex;gap:6px">
        <button class="btn btn-ghost btn-sm" onclick="verDetalhesEquipamento(${e.id})">🔍 Detalhes</button>
        <button class="btn btn-ghost btn-sm" onclick="editarEquipamentoInv(${e.id})">✏️</button>
      </div>
    </td>
  </tr>`;
}

async function loadMovimentacoes() {
  const tbody = document.getElementById('mov-tbody');
  if (!tbody) return;
  try {
    const res   = await fetch('/api/movimentacoes');
    const lista = await res.json();
    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:var(--text-muted);padding:20px">Nenhuma movimentação registrada.</td></tr>`;
      return;
    }
    tbody.innerHTML = lista.map(m => `<tr>
      <td>${m.criado_em}</td>
      <td><strong>${m.equipamento}</strong></td>
      <td>${m.tipo === 'entrada'
        ? `<span class="badge badge-devolvido">📥 Entrada</span>`
        : `<span class="badge badge-atrasado">📤 Saída</span>`}</td>
      <td>${m.quantidade}</td>
      <td>${m.motivo || '—'}</td>
      <td>${m.responsavel || '—'}</td>
    </tr>`).join('');
  } catch (err) { console.error('Erro movimentações:', err); }
}

async function carregarCategoriasSelect() {
  try {
    const res   = await fetch('/api/categorias');
    const lista = await res.json();
    const sel   = document.getElementById('filtro-categoria');
    if (!sel) return;
    const atual = sel.value;
    sel.innerHTML = '<option value="">Todas as categorias</option>' +
      lista.map(c => `<option value="${c.id}" ${atual == c.id ? 'selected' : ''}>${c.icone} ${c.nome}</option>`).join('');
  } catch (e) { console.error(e); }
}

async function carregarCategoriasModalSelect(selectId) {
  try {
    const res   = await fetch('/api/categorias');
    const lista = await res.json();
    const sel   = document.getElementById(selectId);
    if (!sel) return;
    sel.innerHTML = '<option value="">Selecione...</option>' +
      lista.map(c => `<option value="${c.id}">${c.icone} ${c.nome}</option>`).join('');
  } catch (e) { console.error(e); }
}

function setFiltroInv(el, tipo) {
  filtroInvTipo = tipo; filtroInvAlerta = false; filtroInvGarantia = false;
  document.querySelectorAll('#page-inventario .filter-chips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadInventario();
}

function setFiltroInvAlerta(el) {
  filtroInvTipo = ''; filtroInvAlerta = true; filtroInvGarantia = false;
  document.querySelectorAll('#page-inventario .filter-chips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadInventario();
}

function setFiltroGarantia(el) {
  filtroInvTipo = ''; filtroInvAlerta = false; filtroInvGarantia = true;
  document.querySelectorAll('#page-inventario .filter-chips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadInventario();
}

function openModalEquipamentoInv() {
  document.getElementById('equip-inv-id').value = '';
  document.getElementById('equip-inv-title').textContent = '📦 Novo Item no Inventário';
  document.getElementById('form-equip-inv').reset();
  carregarCategoriasModalSelect('inv-categoria');
  document.getElementById('modal-equip-inv').classList.add('open');
}

function closeModalEquipamentoInv() {
  document.getElementById('modal-equip-inv').classList.remove('open');
}

async function editarEquipamentoInv(id) {
  try {
    const res = await fetch(`/api/inventario/${id}`);
    const e   = await res.json();
    if (!e) return;
    document.getElementById('equip-inv-id').value          = e.id;
    document.getElementById('equip-inv-title').textContent = '✏️ Editar Item';
    document.getElementById('inv-nome').value              = e.nome;
    document.getElementById('inv-patrimonio').value        = e.patrimonio === '—' ? '' : e.patrimonio;
    document.getElementById('inv-tipo').value              = e.tipo;
    document.getElementById('inv-quantidade').value        = e.quantidade;
    document.getElementById('inv-qtd-min').value           = e.quantidade_minima;
    document.getElementById('inv-localizacao').value       = e.localizacao === '—' ? '' : e.localizacao;
    document.getElementById('inv-fornecedor').value        = e.fornecedor === '—' ? '' : e.fornecedor;
    document.getElementById('inv-nota-fiscal').value       = e.nota_fiscal === '—' ? '' : e.nota_fiscal;
    document.getElementById('inv-contrato').value          = e.contrato_manutencao === '—' ? '' : e.contrato_manutencao;
    document.getElementById('inv-valor').value             = e.valor_compra || '';
    document.getElementById('inv-descricao').value         = e.descricao || '';
    await carregarCategoriasModalSelect('inv-categoria');
    if (e.categoria_id) document.getElementById('inv-categoria').value = e.categoria_id;
    document.getElementById('modal-equip-inv').classList.add('open');
  } catch (err) { console.error(err); }
}

async function salvarEquipamentoInv(event) {
  event.preventDefault();
  const id = document.getElementById('equip-inv-id').value;
  const payload = {
    nome:                document.getElementById('inv-nome').value,
    patrimonio:          document.getElementById('inv-patrimonio').value,
    categoria_id:        document.getElementById('inv-categoria').value || null,
    tipo:                document.getElementById('inv-tipo').value,
    quantidade:          document.getElementById('inv-quantidade').value,
    quantidade_minima:   document.getElementById('inv-qtd-min').value,
    localizacao:         document.getElementById('inv-localizacao').value,
    fornecedor:          document.getElementById('inv-fornecedor').value,
    nota_fiscal:         document.getElementById('inv-nota-fiscal').value,
    contrato_manutencao: document.getElementById('inv-contrato').value,
    data_compra:         document.getElementById('inv-data-compra').value,
    garantia_ate:        document.getElementById('inv-garantia').value,
    valor_compra:        document.getElementById('inv-valor').value,
    descricao:           document.getElementById('inv-descricao').value
  };
  try {
    let res;
    if (id) {
      res = await fetch(`/api/inventario/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/equipamentos', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    }
    const d = await res.json();
    if (d.success) {
      toast(id ? 'Item atualizado!' : 'Item cadastrado!');
      closeModalEquipamentoInv();
      loadInventario();
    } else {
      toast('Erro: ' + d.error, 'error');
    }
  } catch { toast('Erro de conexão.', 'error'); }
}

function openModalMovimentacao() {
  document.getElementById('form-mov').reset();
  const wrapper = document.getElementById('mov-equip-wrapper');
  wrapper.innerHTML = '';
  carregarBuscaEquipamento('mov-equip-wrapper', 'mov-equipamento-id');
  document.getElementById('modal-movimentacao').classList.add('open');
}

function closeModalMovimentacao() {
  document.getElementById('modal-movimentacao').classList.remove('open');
}

async function salvarMovimentacao(event) {
  event.preventDefault();
  const equipId = document.getElementById('mov-equipamento-id')?.value;
  if (!equipId) { toast('Selecione um equipamento.', 'error'); return; }
  const payload = {
    equipamento_id: equipId,
    tipo:           document.getElementById('mov-tipo').value,
    quantidade:     document.getElementById('mov-quantidade').value,
    motivo:         document.getElementById('mov-motivo').value,
    responsavel:    document.getElementById('mov-responsavel').value,
    observacoes:    document.getElementById('mov-obs').value
  };
  try {
    const res = await fetch('/api/movimentacoes', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
    });
    const d = await res.json();
    if (d.success) {
      toast(`Movimentação registrada! Estoque atual: ${d.quantidade_atual}`);
      closeModalMovimentacao();
      loadInventario();
    } else {
      toast('Erro: ' + d.error, 'error');
    }
  } catch { toast('Erro de conexão.', 'error'); }
}

async function verDetalhesEquipamento(id) {
  try {
    const res   = await fetch(`/api/inventario/${id}`);
    const e     = await res.json();
    alert(`📦 ${e.nome}\n\nPatrimônio: ${e.patrimonio}\nFornecedor: ${e.fornecedor}\nNota Fiscal: ${e.nota_fiscal}\nContrato: ${e.contrato_manutencao}\nCompra: ${e.data_compra || '—'}\nGarantia até: ${e.garantia_ate || '—'}\nValor: ${e.valor_compra ? 'R$ ' + e.valor_compra.toFixed(2) : '—'}`);
  } catch (err) { console.error(err); }
}

// ══════════════════ MANUTENÇÕES ══════════════════

let filtroManStatus = '';

async function loadManutencoes() {
  const tbody = document.getElementById('man-tbody');
  if (!tbody) return;
  tbody.innerHTML = `<tr><td colspan="9" class="loading-cell"><span class="loading-spinner"></span></td></tr>`;
  try {
    const resR   = await fetch('/api/manutencoes/resumo');
    const resumo = await resR.json();
    document.getElementById('man-em').textContent         = resumo.em_manutencao;
    document.getElementById('man-concluidas').textContent = resumo.concluidas;
    document.getElementById('man-custo').textContent      = `R$ ${resumo.custo_total.toFixed(2)}`;
    let url = '/api/manutencoes?';
    if (filtroManStatus) url += `status=${filtroManStatus}`;
    const res   = await fetch(url);
    const lista = await res.json();
    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="9" class="loading-cell">
        <div class="empty-state"><div class="icon">🔧</div>
        <h3>Nenhuma manutenção registrada</h3>
        <p>Registre manutenções para acompanhar o histórico.</p>
        </div></td></tr>`;
      return;
    }
    tbody.innerHTML = lista.map(m => rowManHTML(m)).join('');
  } catch (err) { console.error('Erro manutenções:', err); }
}

function rowManHTML(m) {
  const statusBadge = {
    'em_manutencao': `<span class="badge badge-atrasado badge-pulse">🔧 Em Manutenção</span>`,
    'concluida':     `<span class="badge badge-devolvido">✓ Concluída</span>`,
    'cancelada':     `<span class="badge" style="background:var(--bg-card2);color:var(--text-muted)">✕ Cancelada</span>`
  }[m.status] || '';

  const tipoBadge = {
    'corretiva':  `<span style="color:var(--atrasado);font-size:12px;font-weight:600">🔴 Corretiva</span>`,
    'preventiva': `<span style="color:#F47920;font-size:12px;font-weight:600">🟡 Preventiva</span>`,
    'garantia':   `<span style="color:var(--devolvido);font-size:12px;font-weight:600">🟢 Garantia</span>`
  }[m.tipo] || '';

  const acoes = m.status === 'em_manutencao'
    ? `<button class="btn btn-success btn-sm" onclick="concluirManutencao(${m.id})">✓ Concluir</button>
       <button class="btn btn-danger btn-sm" onclick="cancelarManutencao(${m.id})">✕</button>`
    : `<span style="color:var(--text-dim);font-size:12px">—</span>`;

  return `<tr>
    <td><strong>${m.equipamento}</strong><br><small style="color:var(--text-muted)">${m.patrimonio}</small></td>
    <td>${tipoBadge}</td>
    <td style="max-width:200px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="${m.descricao}">${m.descricao}</td>
    <td>${m.tecnico}<br><small style="color:var(--text-muted)">${m.empresa}</small></td>
    <td>${m.data_entrada}</td>
    <td>${m.data_saida || '—'}</td>
    <td>${m.custo ? `R$ ${m.custo.toFixed(2)}` : '—'}</td>
    <td>${statusBadge}</td>
    <td><div style="display:flex;gap:6px">${acoes}</div></td>
  </tr>`;
}

function setFiltroMan(el, status) {
  filtroManStatus = status;
  document.querySelectorAll('#page-manutencoes .filter-chips .chip').forEach(c => c.classList.remove('active'));
  el.classList.add('active');
  loadManutencoes();
}

function openModalManutencao() {
  document.getElementById('man-modal-id').value = '';
  document.getElementById('man-modal-title').textContent = '🔧 Nova Manutenção';
  document.getElementById('form-man').reset();
  const now = new Date();
  const pad = n => String(n).padStart(2,'0');
  const dt  = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
  document.getElementById('man-entrada').value = dt;
  carregarBuscaEquipamento('man-equip-wrapper', 'man-equipamento-id');
  document.getElementById('modal-manutencao').classList.add('open');
}

function closeModalManutencao() {
  document.getElementById('modal-manutencao').classList.remove('open');
}

async function salvarManutencao(event) {
  event.preventDefault();
  const id      = document.getElementById('man-modal-id').value;
  const equipId = document.getElementById('man-equipamento-id')?.value;
  if (!equipId) { toast('Selecione um equipamento.', 'error'); return; }
  const payload = {
    equipamento_id: equipId,
    tipo:           document.getElementById('man-tipo').value,
    status:         document.getElementById('man-status').value,
    tecnico:        document.getElementById('man-tecnico').value,
    empresa:        document.getElementById('man-empresa').value,
    data_entrada:   document.getElementById('man-entrada').value,
    data_saida:     document.getElementById('man-saida').value,
    custo:          document.getElementById('man-custo-input').value,
    descricao:      document.getElementById('man-descricao').value,
    observacoes:    document.getElementById('man-obs').value
  };
  try {
    let res;
    if (id) {
      res = await fetch(`/api/manutencoes/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/manutencoes', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    }
    const d = await res.json();
    if (d.success) {
      toast(id ? 'Manutenção atualizada!' : 'Manutenção registrada!');
      closeModalManutencao();
      loadManutencoes();
    } else {
      toast('Erro: ' + d.error, 'error');
    }
  } catch { toast('Erro de conexão.', 'error'); }
}

async function concluirManutencao(id) {
  if (!confirm('Marcar manutenção como concluída?')) return;
  try {
    await fetch(`/api/manutencoes/${id}/concluir`, { method: 'POST' });
    toast('Manutenção concluída!');
    loadManutencoes();
  } catch { toast('Erro.', 'error'); }
}

async function cancelarManutencao(id) {
  if (!confirm('Cancelar esta manutenção?')) return;
  try {
    await fetch(`/api/manutencoes/${id}`, { method: 'DELETE' });
    toast('Manutenção cancelada.');
    loadManutencoes();
  } catch { toast('Erro.', 'error'); }
}

// ══════════════════ BUSCA EQUIPAMENTO REUTILIZÁVEL ══════════════════

async function carregarBuscaEquipamento(wrapperId, hiddenId) {
  try {
    const res   = await fetch('/api/equipamentos');
    const lista = await res.json();
    window._equipsGlobal = lista;
    const wrapper = document.getElementById(wrapperId);
    if (!wrapper) return;
    wrapper.innerHTML = `
      <div style="position:relative">
        <input type="text" id="${hiddenId}-busca" placeholder="🔍 Digite o nome ou patrimônio..."
          autocomplete="off"
          oninput="filtrarBuscaEquip(this, '${hiddenId}', window._equipsGlobal)"
          onfocus="document.getElementById('${hiddenId}-dd').style.display='block'"
          style="width:100%">
        <input type="hidden" id="${hiddenId}" required>
        <div id="${hiddenId}-dd" style="display:none;position:absolute;top:100%;left:0;right:0;
          background:var(--bg-card);border:1px solid var(--border-hover);border-radius:var(--radius-sm);
          max-height:180px;overflow-y:auto;z-index:999;box-shadow:var(--shadow);margin-top:4px"></div>
      </div>`;
    preencherBuscaDropdown(hiddenId, lista);
    document.addEventListener('click', function(e) {
      const w = document.getElementById(wrapperId);
      if (w && !w.contains(e.target)) {
        const dd = document.getElementById(`${hiddenId}-dd`);
        if (dd) dd.style.display = 'none';
      }
    });
  } catch (e) { console.error(e); }
}

function preencherBuscaDropdown(hiddenId, lista) {
  const dd = document.getElementById(`${hiddenId}-dd`);
  if (!dd) return;
  const disponiveis = lista.filter(e => !e.emprestado);
  if (!disponiveis.length) {
    dd.innerHTML = `<div style="padding:12px 16px;color:var(--text-muted);font-size:13px">Nenhum equipamento disponível</div>`;
    return;
  }
  dd.innerHTML = disponiveis.map(e => `
    <div onclick="selecionarEquipBusca('${hiddenId}', ${e.id}, '${e.nome}', '${e.patrimonio}')"
      style="padding:10px 16px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--border)"
      onmouseover="this.style.background='var(--bg-card2)'"
      onmouseout="this.style.background='transparent'">
      <strong>${e.nome}</strong>
      <span style="color:var(--text-muted);margin-left:8px">${e.patrimonio}</span>
    </div>`).join('');
}

function filtrarBuscaEquip(input, hiddenId, lista) {
  document.getElementById(`${hiddenId}-dd`).style.display = 'block';
  document.getElementById(hiddenId).value = '';
  const t = input.value.toLowerCase();
  const filtrado = (lista || []).filter(e =>
    !e.emprestado &&
    (e.nome.toLowerCase().includes(t) || e.patrimonio.toLowerCase().includes(t))
  );
  preencherBuscaDropdown(hiddenId, filtrado);
}

function selecionarEquipBusca(hiddenId, id, nome, patrimonio) {
  document.getElementById(hiddenId).value           = id;
  document.getElementById(`${hiddenId}-busca`).value = `${nome} — ${patrimonio}`;
  document.getElementById(`${hiddenId}-dd`).style.display = 'none';
}

// ══════════════════ AUTH ══════════════════

async function carregarUsuarioLogado() {
  try {
    const res = await fetch('/api/auth/me');
    if (res.status === 401) {
      window.location.href = '/login';
      return;
    }
    const u = await res.json();
    document.getElementById('usuario-nome').textContent  = u.nome;
    document.getElementById('usuario-nivel').textContent = u.nivel === 'admin' ? '👑 Admin' : '🔧 Técnico';
    if (u.nivel === 'admin') {
      const menuUsr = document.getElementById('menu-usuarios');
      if (menuUsr) menuUsr.style.display = 'block';
    }
  } catch (e) { console.error(e); }
}

async function fazerLogout() {
  if (!confirm('Deseja sair do sistema?')) return;
  try {
    await fetch('/api/auth/logout', { method: 'POST' });
    window.location.href = '/login';
  } catch {
    window.location.href = '/login';
  }
}

// ══════════════════ USUÁRIOS ══════════════════

async function loadUsuarios() {
  const tbody = document.getElementById('usr-tbody');
  if (!tbody) return;
  try {
    const res   = await fetch('/api/usuarios');
    const lista = await res.json();
    if (!lista.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="loading-cell">
        <div class="empty-state"><div class="icon">👥</div>
        <h3>Nenhum usuário cadastrado</h3></div></td></tr>`;
      return;
    }
    tbody.innerHTML = lista.map(u => `<tr>
      <td><strong>${u.nome}</strong></td>
      <td>${u.email}</td>
      <td>${u.nivel === 'admin' ? '👑 Admin' : '🔧 Técnico'}</td>
      <td>${u.ultimo_acesso}</td>
      <td><span class="badge ${u.ativo ? 'badge-devolvido' : 'badge-atrasado'}">${u.ativo ? '● Ativo' : '○ Inativo'}</span></td>
      <td style="display:flex;gap:6px">
        <button class="btn btn-ghost btn-sm" onclick="editarUsuario(${u.id}, '${u.nome}', '${u.email}', '${u.nivel}')">✏️ Editar</button>
        <button class="btn btn-danger btn-sm" onclick="toggleUsuario(${u.id}, ${u.ativo})">${u.ativo ? '🗑 Desativar' : '♻️ Ativar'}</button>
      </td>
    </tr>`).join('');
  } catch (e) {
    tbody.innerHTML = `<tr><td colspan="6" style="color:var(--atrasado);padding:20px;text-align:center">Erro ao carregar.</td></tr>`;
  }
}

function openModalUsuario() {
  document.getElementById('usr-modal-id').value = '';
  document.getElementById('usr-modal-title').textContent = '👥 Novo Usuário';
  document.getElementById('usr-senha-label').textContent = 'Senha *';
  document.getElementById('usr-senha').required = true;
  document.getElementById('form-usr').reset();
  document.getElementById('modal-usuario').classList.add('open');
}

function closeModalUsuario() {
  document.getElementById('modal-usuario').classList.remove('open');
}

function editarUsuario(id, nome, email, nivel) {
  document.getElementById('usr-modal-id').value          = id;
  document.getElementById('usr-modal-title').textContent = '✏️ Editar Usuário';
  document.getElementById('usr-senha-label').textContent = 'Nova Senha (deixe em branco para não alterar)';
  document.getElementById('usr-senha').required          = false;
  document.getElementById('usr-nome').value              = nome;
  document.getElementById('usr-email').value             = email;
  document.getElementById('usr-nivel').value             = nivel;
  document.getElementById('usr-senha').value             = '';
  document.getElementById('modal-usuario').classList.add('open');
}

async function salvarUsuario(event) {
  event.preventDefault();
  const id = document.getElementById('usr-modal-id').value;
  const payload = {
    nome:  document.getElementById('usr-nome').value,
    email: document.getElementById('usr-email').value,
    nivel: document.getElementById('usr-nivel').value,
    senha: document.getElementById('usr-senha').value
  };
  try {
    let res;
    if (id) {
      res = await fetch(`/api/usuarios/${id}`, {
        method: 'PUT', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/usuarios', {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
      });
    }
    const d = await res.json();
    if (d.success) {
      toast(id ? 'Usuário atualizado!' : 'Usuário cadastrado!');
      closeModalUsuario();
      loadUsuarios();
    } else {
      toast('Erro: ' + d.error, 'error');
    }
  } catch { toast('Erro de conexão.', 'error'); }
}

async function toggleUsuario(id, ativo) {
  if (!confirm(ativo ? 'Desativar este usuário?' : 'Reativar este usuário?')) return;
  try {
    await fetch(`/api/usuarios/${id}`, {
      method: 'PUT', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ ativo: !ativo })
    });
    toast(ativo ? 'Usuário desativado.' : 'Usuário reativado!');
    loadUsuarios();
  } catch { toast('Erro.', 'error'); }
}

// ══════════════════ TEMA ══════════════════

function alternarTema() {
  const body = document.body;
  const btn  = document.getElementById('btn-tema');
  const temaClaro = body.classList.toggle('tema-claro');

  if (temaClaro) {
    btn.textContent = '🌙 Tema Escuro';
    btn.style.color = '#4A5568';
    btn.style.background = 'rgba(0,0,0,0.05)';
    btn.style.borderColor = 'rgba(0,0,0,0.12)';
    localStorage.setItem('tema', 'claro');
  } else {
    btn.textContent = '☀️ Tema Claro';
    btn.style.color = '#60B8FF';
    btn.style.background = 'rgba(0,102,179,0.1)';
    btn.style.borderColor = 'rgba(0,102,179,0.3)';
    localStorage.setItem('tema', 'escuro');
  }
}

function carregarTema() {
  const tema = localStorage.getItem('tema');
  if (tema === 'claro') {
    document.body.classList.add('tema-claro');
    const btn = document.getElementById('btn-tema');
    if (btn) {
      btn.textContent = '🌙 Tema Escuro';
      btn.style.color = '#4A5568';
      btn.style.background = 'rgba(0,0,0,0.05)';
      btn.style.borderColor = 'rgba(0,0,0,0.12)';
    }
  }
}

// ══════════════════ INICIALIZAÇÃO ══════════════════

document.addEventListener('DOMContentLoaded', () => {
  carregarTema();
  carregarUsuarioLogado();
  navigate('dashboard');
  setInterval(() => {
    const paginaAtiva = document.querySelector('.page.active')?.id?.replace('page-', '');
    if (paginaAtiva) loadPage(paginaAtiva);
  }, 60000);
});