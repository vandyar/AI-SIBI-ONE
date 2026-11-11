'use strict';

async function loadRecruitmentReport() {
  const positionList = document.getElementById('analytics-position-list');
  const publicSummary = document.getElementById('public-report-summary');
  const publicPositions = document.getElementById('public-report-positions');
  const errorTarget = document.getElementById('public-report-error');

  try {
    const response = await fetch('/api/public/recruitment-report');
    if (!response.ok) throw new Error(`Laporan gagal dimuat (${response.status}).`);
    const report = await response.json();

    const setText = (id, value) => {
      const element = document.getElementById(id);
      if (element) element.textContent = value;
    };
    setText('analytics-screened', report.cvScreened);
    setText('analytics-started', report.interviewsStarted);
    setText('analytics-completed', report.interviewsCompleted);
    setText('analytics-completion-rate', `${report.interviewCompletionRate}%`);
    setText('analytics-updated', `Diperbarui: ${new Date(report.generatedAt).toLocaleString('id-ID')}`);

    if (positionList) {
      positionList.replaceChildren();
      const entries = Object.entries(report.positionStats);
      if (entries.length === 0) {
        positionList.textContent = 'Belum ada data posisi.';
      } else {
        entries.sort(([a], [b]) => a.localeCompare(b, 'id'));
        entries.forEach(([position, stats]) => {
          const row = document.createElement('p');
          row.className = 'rounded bg-white px-3 py-2';
          row.textContent = `${position}: ${stats.total} pelamar · ${stats.completed} interview selesai · ${stats.passed} lolos`;
          positionList.appendChild(row);
        });
      }
    }

    if (publicSummary) {
      publicSummary.replaceChildren();
      [
        ['Total pelamar unik', report.totalApplicants],
        ['CV dianalisis', report.cvScreened],
        ['Interview dimulai', report.interviewsStarted],
        ['Interview selesai', report.interviewsCompleted],
        ['Tingkat penyelesaian interview', `${report.interviewCompletionRate}%`],
        ['Kandidat lolos', report.passedCandidates],
        ['Kelulusan dari interview selesai', `${report.passRate}%`],
        ['Skor rata-rata interview', report.averageScore]
      ].forEach(([label, value]) => {
        const card = document.createElement('article');
        card.className = 'report-card';
        const title = document.createElement('p');
        title.textContent = label;
        const number = document.createElement('strong');
        number.textContent = value;
        card.append(title, number);
        publicSummary.appendChild(card);
      });
    }

    if (publicPositions) {
      publicPositions.replaceChildren();
      const entries = Object.entries(report.positionStats);
      if (entries.length === 0) {
        const row = document.createElement('tr');
        const cell = document.createElement('td');
        cell.colSpan = 7;
        cell.textContent = 'Belum ada data rekrutmen.';
        row.appendChild(cell);
        publicPositions.appendChild(row);
      } else {
        entries.sort(([a], [b]) => a.localeCompare(b, 'id'));
        entries.forEach(([position, stats]) => {
          const row = document.createElement('tr');
          [
            position, stats.total, stats.screened, stats.interviewsStarted,
            stats.completed, stats.passed, `${stats.passRate}%`
          ].forEach(value => {
            const cell = document.createElement('td');
            cell.textContent = value;
            row.appendChild(cell);
          });
          publicPositions.appendChild(row);
        });
      }
    }
    setText('public-report-updated', `Terakhir diperbarui: ${new Date(report.generatedAt).toLocaleString('id-ID')}`);
    if (errorTarget) errorTarget.textContent = '';
  } catch (error) {
    console.error('Gagal memuat laporan rekrutmen', error);
    if (positionList) positionList.textContent = error.message;
    if (errorTarget) errorTarget.textContent = error.message;
  }
}

window.refreshRecruitmentReport = loadRecruitmentReport;

if (document.getElementById('public-report-summary')) {
  loadRecruitmentReport();
}
