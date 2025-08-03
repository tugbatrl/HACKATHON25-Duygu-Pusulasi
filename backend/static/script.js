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





let currentStep = "step1"
let answers = [];


window.collectedAnswers = answers;


function showScenario(stepId){
  const step = scenarios[stepId];
  
  // DOM elementlerini kontrol et
  const scenarioText = document.getElementById('scenario-text');
  const optionsContainer = document.getElementById('options-container');
  
  if (!step) {
    console.error('Senaryo bulunamadı:', stepId);
    if (scenarioText) {
      scenarioText.textContent = 'Senaryo yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.';
    }
    return;
  }
  
  currentStep = stepId;

  if (scenarioText) {
    scenarioText.textContent = step.text;
  }
  
  if (optionsContainer) {
    optionsContainer.innerHTML = "";
  }

  if (step.options && optionsContainer) {
    step.options.forEach(option => {
      const button = document.createElement("button");
      button.textContent = option.text;
      button.className = 'option-btn';
      button.onclick = () => {
        saveAnswerAndContinue(stepId, option.value);
      };
      optionsContainer.appendChild(button);
    });
  }

  if (stepId === "end") {
    // Sadece tamamlandı mesajını göster
    if (scenarioText) {
      scenarioText.textContent = "Oyun tamamlandı! Rapor öğretmenine gönderildi.";
    }
    if (optionsContainer) {
      optionsContainer.innerHTML = "";
    }
    
    // Raporu arka planda oluştur
    generateReportSilently();
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
  const optionsContainer = document.getElementById('options-container');
  const scenarioText = document.getElementById('scenario-text');
  
  if (optionsContainer) {
    optionsContainer.innerHTML = "";
  }
  
  // Sadece tamamlandı mesajını göster
  if (scenarioText) {
    scenarioText.textContent = "Oyun tamamlandı! Rapor öğretmenine gönderildi.";
  }
  
  // Raporu arka planda oluştur ama gösterme
  generateReportSilently();
}

function generateReportSilently() {
  const answers = window.collectedAnswers || [];
  
  // Cevapları progress formatına çevir
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
      // Raporu session'a kaydet ama gösterme
      saveReportToSession({
        report: data.report_text || 'Rapor oluşturuldu!',
        answers: answers
      });
      console.log('Rapor başarıyla oluşturuldu ve kaydedildi.');
    } else {
      console.error('Rapor oluşturma hatası:', data.message);
    }
  })
  .catch(error => {
    console.error('Rapor oluşturma hatası:', error);
  });
}


function loadNextStep() {
 
  loadScenarios();
}




