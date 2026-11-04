const el = (id) => document.getElementById(id);
let accepted = false;
let deleted = false;
const demoSource = el('lecture').value;
const demoQuestions = el('questions').value;
el('source-text').textContent = demoSource;

function route() {
  const requested = location.hash.slice(1);
  const target = ['upload', 'approve', 'review'].includes(requested) ? requested : 'upload';
  document.querySelectorAll('.screen').forEach((screen) => { screen.hidden = screen.id !== target; });
  document.querySelectorAll('nav a').forEach((link) => {
    if (link.hash === `#${target}`) link.setAttribute('aria-current', 'page');
    else link.removeAttribute('aria-current');
  });
  el('feedback').textContent = '';
  el('review-card').hidden = !accepted || deleted;
  el('review-summary').textContent = accepted && !deleted
    ? 'Одна демонстрационная карточка. Результаты не сохраняются после перезагрузки.'
    : 'Нет карточек для повторения. Сначала прими карточку на экране проверки.';
}
window.addEventListener('hashchange', route);
el('upload-form').addEventListener('submit', (event) => {
  event.preventDefault();
  if (el('lecture').value.trim() !== demoSource.trim() || el('questions').value.trim() !== demoQuestions.trim()) {
    el('feedback').textContent = 'Прототип не генерирует карточки для нового текста или вопросов. Верни исходный пример для демонстрации.';
    return;
  }
  el('source-title').textContent = el('title').value;
  accepted = false;
  deleted = false;
  el('card-status').textContent = 'Черновик';
  location.hash = 'approve';
});
el('accept').addEventListener('click', () => {
  if (!el('card-question').value.trim() || !el('card-answer').value.trim()) {
    el('feedback').textContent = 'Заполни вопрос и эталонный ответ.';
    return;
  }
  accepted = true;
  deleted = false;
  el('card-status').textContent = 'Принята';
  el('review-question').textContent = el('card-question').value;
  el('reference-answer').textContent = el('card-answer').value;
  el('reference').hidden = true;
  el('student-answer').value = '';
  el('feedback').textContent = 'Карточка принята. Открой «Повторить сегодня».';
});
el('delete').addEventListener('click', () => {
  deleted = true;
  accepted = false;
  el('card-status').textContent = 'Удалена';
  el('feedback').textContent = 'Карточка исключена из повторения. Её можно снова принять.';
});
el('reveal').addEventListener('click', () => {
  if (!el('student-answer').value.trim()) {
    el('feedback').textContent = 'Сначала попробуй написать ответ.';
    return;
  }
  el('reference').hidden = false;
  el('feedback').textContent = '';
});
document.querySelectorAll('[data-grade]').forEach((button) => {
  button.addEventListener('click', () => {
    const message = { correct: 'Верно', partial: 'Частично', incorrect: 'Неверно' }[button.dataset.grade];
    el('review-card').hidden = true;
    el('review-summary').textContent = `Самооценка: ${message}. Демонстрационное повторение завершено.`;
    el('feedback').textContent = 'В MVP результат определит следующую дату. В прототипе расписание не рассчитывается.';
  });
});
route();
