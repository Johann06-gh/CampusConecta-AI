const form = document.querySelector('#questionForm');
const input = document.querySelector('#questionInput');
const messages = document.querySelector('#messages');
const sendButton = document.querySelector('#sendButton');
const clearButton = document.querySelector('#clearButton');
const statusBadge = document.querySelector('#statusBadge');
const documentName = document.querySelector('#documentName');
const documentMeta = document.querySelector('#documentMeta');

function escapeHtml(value) {
  return value.replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#039;', '"': '&quot;'
  })[char]);
}

function renderMarkdownLite(value) {
  let safe = escapeHtml(value);
  safe = safe.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  safe = safe.replace(/_(.*?)_/g, '<em>$1</em>');
  const lines = safe.split('\n');
  let output = '';
  let inList = false;
  for (const line of lines) {
    if (line.startsWith('- ')) {
      if (!inList) { output += '<ul>'; inList = true; }
      output += `<li>${line.slice(2)}</li>`;
    } else {
      if (inList) { output += '</ul>'; inList = false; }
      if (line.trim()) output += `<p>${line}</p>`;
    }
  }
  if (inList) output += '</ul>';
  return output;
}

function addMessage(role, content, sources = []) {
  const article = document.createElement('article');
  article.className = `message ${role}`;
  const sourceHtml = sources.length ? `
    <div class="source-list">
      ${sources.map(source => `
        <div class="source-card">
          <strong>${escapeHtml(source.title)}</strong>
          <span>${escapeHtml(source.category || source.file)} · relevancia ${Math.round(source.relevance * 100)}%</span>
          ${source.contact ? `<span>${escapeHtml(source.contact)}</span>` : ''}
          ${source.url ? `<a href="${escapeHtml(source.url)}" target="_blank" rel="noopener">Abrir referencia</a>` : ''}
        </div>`).join('')}
    </div>` : '';
  article.innerHTML = role === 'assistant'
    ? `<div class="avatar">AI</div><div class="bubble">${renderMarkdownLite(content)}${sourceHtml}</div>`
    : `<div class="bubble"><p>${escapeHtml(content)}</p></div>`;
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function setLoading(active) {
  sendButton.disabled = active;
  input.disabled = active;
  sendButton.querySelector('span:first-child').textContent = active ? 'Pensando' : 'Enviar';
}

async function askQuestion(question) {
  addMessage('user', question);
  const typing = addMessage('assistant', 'Buscando la información más relevante...');
  typing.querySelector('.bubble').classList.add('typing');
  setLoading(true);

  try {
    const response = await fetch('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || 'Error inesperado');
    typing.remove();
    addMessage('assistant', payload.answer, payload.sources);
  } catch (error) {
    typing.remove();
    addMessage('assistant', `No pude completar la consulta. ${error.message}`);
  } finally {
    setLoading(false);
    input.focus();
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const question = input.value.trim();
  if (!question) return;
  input.value = '';
  input.style.height = 'auto';
  askQuestion(question);
});

input.addEventListener('input', () => {
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 150)}px`;
});

input.addEventListener('keydown', event => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

document.querySelectorAll('#suggestions button').forEach(button => {
  button.addEventListener('click', () => {
    input.value = button.textContent;
    form.requestSubmit();
  });
});

clearButton.addEventListener('click', () => {
  messages.innerHTML = '';
  addMessage('assistant', 'Conversación reiniciada. ¿Qué servicio deseas consultar?');
});

async function loadStatus() {
  try {
    const [healthResponse, summaryResponse] = await Promise.all([
      fetch('/api/health'), fetch('/api/document-summary')
    ]);
    const health = await healthResponse.json();
    const summary = await summaryResponse.json();
    statusBadge.classList.add('online');
    statusBadge.innerHTML = `<span></span> ${health.llm_enabled ? 'Gemini conectado' : 'Modo demostración'}`;
    documentName.textContent = summary.document;
    documentMeta.textContent = `${summary.records} registros · ${summary.categories.length} categorías`;
  } catch (_) {
    statusBadge.innerHTML = '<span></span> Servicio no disponible';
    documentName.textContent = 'No disponible';
    documentMeta.textContent = 'Revisa el servidor';
  }
}

loadStatus();
