const questionInput = document.getElementById('question-input');
const generateBtn = document.getElementById('generate-btn');
const sqlDisplay = document.getElementById('sql-display');
const textOutput = document.getElementById('text-output');
const exampleChips = document.querySelectorAll('.example-chip');

generateBtn.addEventListener('click', generateSQL);

exampleChips.forEach(chip => {
  chip.addEventListener('click', () => {
    questionInput.value = chip.textContent;
    generateSQL();
  });
});

questionInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    generateSQL();
  }
});

function generateSQL() {
  const question = questionInput.value;
  sqlDisplay.textContent = '...';
  textOutput.innerHTML = '';

  fetch("/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question })
  })
    .then(res => res.json())
    .then(data => {
      sqlDisplay.textContent = data.sql || 'لم يتم توليد استعلام.';
      if (data.result?.error) {
        textOutput.innerHTML = `<div style="color:red">${data.result.error}</div>`;
      } else {
        renderResults(data.result);
      }
    })
    .catch(err => {
      textOutput.innerHTML = `<div style="color:red">فشل في الاتصال بالخادم: ${err.message}</div>`;
    });
}

function renderResults(rows) {
    const table = document.getElementById("results-table");
    const singleResult = document.getElementById("single-result");
    table.innerHTML = "";
    singleResult.innerHTML = "";

    if (rows.error) {
        table.innerHTML = `<tr><td colspan="100%">خطأ: ${rows.error}</td></tr>`;
        return;
    }

    if (rows.length === 0) {
        table.innerHTML = `<tr><td colspan="100%">لا توجد نتائج</td></tr>`;
        return;
    }

    const keys = Object.keys(rows[0]);

    // ✅ إذا كانت النتيجة عبارة عن قيمة واحدة فقط
    if (keys.length === 1 && rows.length === 1) {
        const col = keys[0];
        const val = rows[0][col];
        singleResult.innerHTML = `النتيجة: <span style="color:#b21f1f">${val}</span>`;
        return;
    }

    // ✅ عرض جدول كامل
    const thead = `<tr>${keys.map(h => `<th>${h}</th>`).join('')}</tr>`;
    const tbody = rows.map(row =>
        `<tr>${keys.map(h => `<td>${row[h]}</td>`).join('')}</tr>`
    ).join('');
    table.innerHTML = thead + tbody;
}


