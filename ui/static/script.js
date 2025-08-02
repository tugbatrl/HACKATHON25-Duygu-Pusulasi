// 
function saveReportToSession(reportData) {

  console.log('Rapor API\'ye gönderildi ve kaydedildi:', reportData);
}

let scenarios = {};


function loadScenarios() {
  
  fetch('/api/student-progress')
    .then(response => {
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      return response.json();
    })
    .then(progressData => {
     
      return fetch('/api/scenarios')
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }
          return response.json();
        })
        .then(scenariosData => {
          return { progress: progressData, scenarios: scenariosData };
        });
    })
    .then(data => {
      if (data.scenarios.error) {
        console.error('Senaryo yükleme hatası:', data.scenarios.error);
        scenarioText.textContent = 'Senaryolar yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.';
        return;
      }
      
      // API'den gelen senaryoları JavaScript formatına çevir
      scenarios = {};
      Object.keys(data.scenarios).forEach(stepKey => {
        const step = data.scenarios[stepKey];
        scenarios[stepKey] = {
          text: step.question,
          options: Object.keys(step.options).map(key => ({
            text: step.options[key],
            value: key
          })),
          next_step: stepKey === 'step4' ? 'end' : `step${parseInt(stepKey.replace('step', '')) + 1}`
        };
      });
      
      
      scenarios.end = {
        text: 'Senaryo tamamlandı! Şimdi raporunu oluşturuyoruz...',
        options: [],
        next_step: 'report'
      };
      
      
      if (data.progress.progress) {
        answers = [];
        Object.keys(data.progress.progress).forEach(stepKey => {
          answers.push({ 
            step: stepKey, 
            choice: data.progress.progress[stepKey] 
          });
        });
        window.collectedAnswers = answers;
      }
      
      
      const currentStep = data.progress.current_step || 'step1';
      showScenario(currentStep);
    })
    .catch(error => {
      console.error('Yükleme hatası:', error);
      scenarioText.textContent = 'Veriler yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.';
    });
}


const scenarioText = document.getElementById("scenario-text");
const optionsContainer = document.getElementById("options-container");
const reportContainer = document.getElementById("report-container");
const teacherReport = document.getElementById("teacher-report-content");
const restartButton = document.getElementById("restart-button");


const scenarioBox = document.getElementById('scenario-box');


let currentStep = "step1"
let answers = [];


window.collectedAnswers = answers;


function showScenario(stepId){
  const step = scenarios[stepId];
  
 
  if (!step) {
    console.error('Senaryo bulunamadı:', stepId);
    scenarioText.textContent = 'Senaryo yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.';
    return;
  }
  
  currentStep = stepId;

  scenarioText.textContent = step.text;
  optionsContainer.innerHTML = "";
  restartButton.style.display = "none";

  step.options.forEach(option => {
    const button = document.createElement("button");
    button.textContent = option.text;
    button.onclick = () => {
      
      saveAnswerAndContinue(stepId, option.value);
    };
    optionsContainer.appendChild(button);
  });

  if (stepId === "end") {
    scenarioText.textContent = step.text;
    optionsContainer.innerHTML = "";
    showReportPlaceholder();

    restartButton.style.display = "block";
  }
}

function saveAnswerAndContinue(stepId, choice) {
 
  fetch('/save-answer', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      step: stepId,
      answer: choice
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    if (data.status === 'success') {
      
      answers.push({ step: stepId, choice: choice });
      window.collectedAnswers = answers;
      
     
      const step = scenarios[stepId];
      if (step && step.next_step) {
        showScenario(step.next_step);
      }
    } else {
      alert(data.message || 'Cevap kaydedilirken bir hata oluştu.');
    }
  })
  .catch(error => {
    console.error('Cevap kaydetme hatası:', error);
    alert('Cevap kaydedilirken bir hata oluştu. Lütfen tekrar deneyin.');
  });
}

function showReportPlaceholder() {
  optionsContainer.innerHTML = "";
  reportContainer.style.display = "block";
  
  
  generateReport();
}

function generateReport() {
  const answers = window.collectedAnswers || [];
  
  
  const progress = {};
  answers.forEach(answer => {
    progress[answer.step] = answer.choice;
  });
  
  fetch('/generate-report', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      progress: progress
    })
  })
  .then(response => {
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  })
  .then(data => {
    if (data.status === 'success') {
     
      teacherReport.textContent = data.report_text || 'Rapor oluşturuldu!';
      
      
      saveReportToSession({
        report: data.report_text || 'Rapor oluşturuldu!',
        answers: answers
      });
    } else {
      teacherReport.textContent = data.message || 'Rapor oluşturulurken bir hata oluştu.';
    }
  })
  .catch(error => {
    console.error('Rapor oluşturma hatası:', error);
    teacherReport.textContent = 'Rapor oluşturulurken bir hata oluştu. Lütfen tekrar deneyin.';
  });
}


function loadNextStep() {
 
  loadScenarios();
}

restartButton.onclick = () => {
  answers = [];
  currentStep = "step1"
  reportContainer.style.display = "none";
  
  loadScenarios();
};



